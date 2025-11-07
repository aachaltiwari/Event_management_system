from rest_framework import serializers
from .models import User, Role, StudentProfile, Club, ClubMember, Event, EventRegistration, Feedback
from django.utils import timezone
from django.contrib.auth.hashers import make_password

#Role Serializer
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['name']



# Student Profile Serializer
class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ['department', 'university_id']



# User Registration Serializer
class UserRegistrationSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'student_profile']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        student_data = validated_data.pop('student_profile', None)
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.password = make_password(password)
        user.save()

        # Create student profile if data provided
        if student_data:
            StudentProfile.objects.create(user=user, **student_data)

        return user


#user profile view serializer
class UserProfileSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'roles', 'student_profile']
        read_only_fields = ['id', 'roles']

    def update(self, instance, validated_data):
        student_data = validated_data.pop('student_profile', None)

        # Update user fields (like email, username)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update student profile if exists
        if student_data:
            StudentProfile.objects.update_or_create(
                user=instance,
                defaults=student_data
            )

        return instance


# Club Creation and Approval Serializer
class ClubSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')

    moderator = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.filter(roles__name='moderator'),
        required=False
    )

    status = serializers.ChoiceField(
        choices=Club.STATUS_CHOICES,
        required=False
    )

    class Meta:
        model = Club
        fields = ['id', 'name', 'description', 'moderator', 'created_by', 'status', 'created_at']
        read_only_fields = ['id', 'created_at', 'created_by']

    def create(self, validated_data):
        """
        When a student creates a club, status should always be 'pending'.
        """
        validated_data['status'] = 'pending'
        return super().create(validated_data)

    def validate_status(self, value):
        club = self.instance
        # Validate only during update (by admin)
        if club and value in ['approved', 'rejected']:
            if not club.moderator:
                raise serializers.ValidationError("Moderator must be assigned before approval.")
            if not club.moderator.has_role('moderator'):
                raise serializers.ValidationError(
                    f"Assigned user '{club.moderator.username}' is not a valid moderator."
                )
        return value
    
    
# club list serializer
class ClubListSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    moderator = serializers.ReadOnlyField(source='moderator.username')
    status = serializers.ReadOnlyField()

    class Meta:
        model = Club
        fields = ['id', 'name', 'description', 'moderator', 'created_by', 'status', 'created_at']
        

# moderator club list serializer(for moderator's view)
class ModeratorClubSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    moderator = serializers.ReadOnlyField(source='moderator.username')

    class Meta:
        model = Club
        fields = ['id', 'name', 'description', 'status', 'created_by', 'moderator', 'created_at']
        read_only_fields = ['id', 'status', 'created_by', 'moderator', 'created_at']
   
    
# Membership application serializer
class ClubMembershipApplySerializer(serializers.ModelSerializer):
    # extra field for applying
    apply = serializers.ChoiceField(
    choices=[('', 'Select...'), ('yes', 'Yes'), ('no', 'No')],
    write_only=True
)


    # club details shown in response
    name = serializers.CharField(source='club.name', read_only=True)
    description = serializers.CharField(source='club.description', read_only=True)
    moderator = serializers.CharField(source='club.moderator.username', read_only=True)

    class Meta:
        model = ClubMember
        fields = ['id', 'club', 'name', 'description', 'moderator', 'apply']
        read_only_fields = ['id', 'club', 'name', 'description', 'moderator']
    
    # convert list input to single value
    def to_internal_value(self, data):
        # Convert ['Yes'] → 'Yes'
        if isinstance(data.get('apply'), list):
            data['apply'] = data['apply'][0]
        return super().to_internal_value(data)
    
    
    def create(self, validated_data):
        user = self.context['request'].user
        club = self.context.get('club')
        apply = validated_data.get('apply')
        if not club:
            raise serializers.ValidationError({"error": "Club not found."})

        # If user selects "no", just return a message
        if apply == 'no':
            raise serializers.ValidationError({"apply": "You chose not to apply for this club."})

        # Prevent duplicate applications
        if ClubMember.objects.filter(user=user, club=club).exists():
            raise serializers.ValidationError({"detail": "You have already applied for this club."})

        return ClubMember.objects.create(user=user, club=club)
    

# Membership request serializer   
class ClubMemberRequestSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    

    class Meta:
        model = ClubMember
        fields = ['id', 'club_name', 'user_name', 'approved']
 
 
# Membership approval serializer   
class ClubMemberApprovalSerializer(serializers.ModelSerializer):
    club = serializers.ReadOnlyField(source='club.name')
    user = serializers.ReadOnlyField(source='user.username')
    approved = serializers.BooleanField(required=True)
    student_details =StudentProfileSerializer(source='user.student_profile', read_only=True)

    class Meta:
        model = ClubMember
        fields = ['id', 'club', 'user', 'student_details', 'approved']
        
        
        
# event serializer
class EventCreateSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.name', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'club', 'club_name', 'title', 'description',
            'date_time', 'venue', 'max_participants', 'fee'
        ]

    def validate(self, attrs):
        user = self.context['request'].user
        club = attrs.get('club')
        date_time = attrs.get('date_time')

        # Check if user is a student member of that club
        if not ClubMember.objects.filter(user=user, club=club, approved=True).exists():
            raise serializers.ValidationError(
                "You must be an approved member of this club to create an event."
            )
            
        # Check if date_time is in the future
        if date_time <= timezone.now():
            raise serializers.ValidationError(
                {"date_time": "Event date and time must be in the future."}
            )

        return attrs

    def create(self, validated_data):
        validated_data['requires_approval'] = True
        validated_data['approved'] = False
        return super().create(validated_data)
    

    
# Pending event list serializer
class PendingEventListSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.name', read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'club_name', 'title']
        
        
        
# pending event approval serializer
class EventApprovalSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.name', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'club_name', 'title', 'description',
            'date_time', 'venue', 'max_participants', 'fee',
            'requires_approval', 'approved'
        ]


# approved events list serializer
class ApprovedEventListSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.name', read_only=True)
    seats_left = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ['id', 'title', 'club_name', 'description', 'date_time', 'venue', 'fee', 'seats_left']

    def get_seats_left(self, obj):
        total_registered = obj.registrations.count()
        return max(obj.max_participants - total_registered, 0)
    
    
# Moderator event list (only those events which are approved by that moderator) serializer
class ModeratorEventSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.name', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'club_name', 'title', 'description',  'date_time', 'venue','max_participants', 'fee', 'approved']
        read_only_fields = ['club_name', 'approved']

    
    
    
# event registration serializer
class EventRegistrationFormSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_description = serializers.CharField(source='event.description', read_only=True)
    event_date = serializers.DateTimeField(source='event.date_time', read_only=True)
    event_venue = serializers.CharField(source='event.venue', read_only=True)
    event_fee = serializers.DecimalField(source='event.fee', read_only=True, max_digits=8, decimal_places=2)
 
    student_name = serializers.CharField(write_only=True)
    university_id = serializers.CharField(write_only=True)
    department = serializers.CharField(write_only=True)
    gmail = serializers.EmailField(write_only=True)

    class Meta:
        model = EventRegistration
        fields = [
            'id', 'event', 
            'event_title', 'event_description', 'event_date', 'event_venue', 'event_fee',
            'student_name', 'university_id', 'department', 'gmail'
        ]
        read_only_fields = ['event']

    def validate(self, attrs):
        user = self.context['request'].user
        event = self.context.get('event')

        # Check if event exists and is approved
        if not event or not event.approved:
            raise serializers.ValidationError("This event is not approved for registration.")

        # Check event date
        if event.date_time <= timezone.now():
            raise serializers.ValidationError("Cannot register for past events.")

        # Check seat availability
        total_registered = event.registrations.count()
        if total_registered >= event.max_participants:
            raise serializers.ValidationError("No seats are available for this event.")

        # Check if already registered
        if EventRegistration.objects.filter(event=event, student=user).exists():
            raise serializers.ValidationError("You have already registered for this event.")

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        event = self.context.get('event')

        # Extract form fields
        student_name = validated_data.pop('student_name')
        university_id = validated_data.pop('university_id')
        department = validated_data.pop('department')
        gmail = validated_data.pop('gmail')

        # Update student's profile if not already filled
        student_profile, _ = StudentProfile.objects.get_or_create(user=user)
        student_profile.department = department
        student_profile.university_id = university_id
        student_profile.save()

        # Ensure user's email matches entered Gmail
        user.email = gmail
        user.save()

        # Register the student for event
        registration = EventRegistration.objects.create(event=event, student=user)

        return registration
    
    
    
# list of event registrations serializer
class EventRegistrationListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.username', read_only=True)
    gmail = serializers.EmailField(source='student.email', read_only=True)
    department = serializers.CharField(source='student.student_profile.department', read_only=True)
    university_id = serializers.CharField(source='student.student_profile.university_id', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    club_name = serializers.CharField(source='event.club.name', read_only=True)

    class Meta:
        model = EventRegistration
        fields = [
            'id', 'event_title', 'club_name',
            'student_name', 'gmail', 'department',
            'university_id', 'registered_at', 'payment_done'
        ]
        
        
        
        
# feedback serializer
class FeedbackSerializer(serializers.ModelSerializer):
    event = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.none(), 
        write_only=True
    )
    rating = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = Feedback
        fields = ['id', 'event', 'rating', 'comments']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, "user"):
            user = request.user
            # Only include past events user registered for and hasn't given feedback
            self.fields['event'].queryset = Event.objects.filter(
                registrations__student=user,
                date_time__lt=timezone.now()  # past events only
            ).exclude(
                registrations__feedback__isnull=False  # exclude events already reviewed
            ).distinct()

    def create(self, validated_data):
        event = validated_data.pop('event')
        user = self.context['request'].user

        registration = EventRegistration.objects.get(event=event, student=user)
        feedback = Feedback.objects.create(registration=registration, **validated_data)
        return feedback



    
# event feedback list serializer
class FeedbacklistSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='registration.student.username', read_only=True)
    event_title = serializers.CharField(source='registration.event.title', read_only=True)
    club_name = serializers.CharField(source='registration.event.club.name', read_only=True)

    class Meta:
        model = Feedback
        fields = ['id', 'event_title', 'club_name', 'student_name', 'rating', 'comments']
        
        
# Total number of registration per event and total amount collected serializer
class EventStatisticsSerializer(serializers.ModelSerializer):
    total_registrations = serializers.IntegerField()
    total_amount_collected = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Event
        fields = ['id', 'title', 'total_registrations', 'total_amount_collected']