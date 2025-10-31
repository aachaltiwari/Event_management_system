from rest_framework import generics, mixins, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import UserRegistrationSerializer, UserProfileSerializer, ClubSerializer, ClubListSerializer, ModeratorClubSerializer, ClubMembershipApplySerializer, ClubMemberApprovalSerializer, ClubMemberRequestSerializer, EventCreateSerializer, PendingEventListSerializer, EventApprovalSerializer, ApprovedEventListSerializer, ModeratorEventSerializer, EventRegistrationFormSerializer, EventRegistrationListSerializer, FeedbackSerializer, FeedbacklistSerializer, EventStatisticsSerializer
from .models import User, Role, Club, ClubMember, Event, EventRegistration, Feedback
from django.shortcuts import get_object_or_404
from .permission import IsStudent, IsModerator, IsAdminRole
from django.utils import timezone
from django.db.models import Count, Sum, F, DecimalField, ExpressionWrapper


# student registration view (open to all)
class StudentRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # Automatically assign student role
        user = serializer.save()
        student_role, _ = Role.objects.get_or_create(name='student')
        user.roles.add(student_role)


# Moderator Registration (admin only)
class ModeratorRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [IsAdminRole]

    def perform_create(self, serializer):
        user = serializer.save()
        moderator_role, _ = Role.objects.get_or_create(name='moderator')
        user.roles.add(moderator_role)


# To view user profile details
class UserProfileView(generics.RetrieveUpdateDestroyAPIView):
    """
    Allows authenticated users (student, moderator, admin)
    to view, update, and delete their own profile.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Always return the current logged-in user
        return self.request.user

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        user.delete()
        return Response({"detail": "Profile deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


# Student creates club (pending approval)
class ClubRequestView(mixins.CreateModelMixin, generics.GenericAPIView):
    serializer_class = ClubSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        # Force created_by and status = pending
        serializer.save(created_by=self.request.user, status='pending')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(
                {"message": "Club request submitted for approval!", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
# Manage club approvals (admin only)
class ClubApprovalView(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    generics.GenericAPIView
):
    queryset = Club.objects.all()
    serializer_class = ClubSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]
    lookup_field = 'id'

    def get_queryset(self):
        # Show only clubs pending approval
        return Club.objects.filter(status='pending')

    def get(self, request, *args, **kwargs):
        # If id provided, show single club detail, else show all pending
        if 'id' in kwargs:
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)

    def put(self, request, *args, **kwargs): 
       # Admin can approve/reject/update a club.
        club = self.get_object()
        serializer = self.get_serializer(club, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        status_value = club.status
        return Response(
            {
                "message": f"Club '{club.name}' has been {status_value} successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )
        
        
# Only logged-In students can see the list of clubs
class StudentClubListView(generics.ListAPIView):
    queryset = Club.objects.filter(status='approved')  # only approved clubs
    serializer_class = ClubListSerializer
    permission_classes = [IsAuthenticated]
    
    
    
# moderator club list view
class ModeratorClubView(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView
):
    # moderators can view list of clubs they moderate, view single club detail, and delete a club
    serializer_class = ModeratorClubSerializer
    permission_classes = [IsAuthenticated, IsModerator]
    lookup_field = 'id'

    def get_queryset(self):
        # Return only clubs where this moderator is assigned
        return Club.objects.filter(moderator=self.request.user)

    def get(self, request, *args, **kwargs):
        if 'id' in kwargs:
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        # Prevent DELETE without ID
        if 'id' not in kwargs:
            return Response(
                {"error": "You must specify a club ID to delete."},
                status=status.HTTP_400_BAD_REQUEST
            )

        club = self.get_object()
        club_name = club.name
        club.delete()
        return Response(
            {"message": f"Club '{club_name}' has been deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )



# Students can apply to join a club
class ClubMembershipApplyView(generics.CreateAPIView):
    serializer_class = ClubMembershipApplySerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        try:
            context['club'] = Club.objects.get(id=self.kwargs['club_id'])
        except Club.DoesNotExist:
            context['club'] = None
        return context

    def get(self, request, club_id):
        #Return club info and apply option
        try:
            club = Club.objects.get(id=club_id)
        except Club.DoesNotExist:
            return Response({"error": "Club not found."}, status=status.HTTP_404_NOT_FOUND)

        data = {
            "club": club.id,
            "name": club.name,
            "description": club.description,
            "moderator": club.moderator.username if club.moderator else None,
            "apply": "yes/no"
        }
        return Response(data)

    def post(self, request, club_id):
        """Handle membership application."""
        try:
            club = Club.objects.get(id=club_id)
        except Club.DoesNotExist:
            return Response({"error": "Club not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data={**request.data, "club": club.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": f"You have successfully applied for {club.name}."}, status=status.HTTP_201_CREATED)
    
    
# Moderator views membership requests for their clubs   
class ClubMemberRequestListView(generics.ListAPIView):
    serializer_class = ClubMemberRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Return only pending membership requests for clubs moderated by the logged-in user
        return ClubMember.objects.filter(
            club__moderator=user,
            approved=False
        )

# MODERATOR APPROVES CLUB MEMBERSHIP REQUEST
class ClubMemberApprovalView(generics.RetrieveUpdateAPIView):
    serializer_class = ClubMemberApprovalSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    #Show student + club details.
    def get_queryset(self):
        # Only clubs moderated by the current user
        return ClubMember.objects.filter(club__moderator=self.request.user)

    
    # PUT → Approve or reject membership and return only message
    def update(self, request, *args, **kwargs):
        club_member = self.get_object()

        approved_status = request.data.get("approved", False)
        if approved_status is None:
            return Response(
                {"error": "Please provide 'approved' status (true/false)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convert string to boolean 
        if isinstance(approved_status, str):
            approved_status = approved_status.lower() in ['true', '1', 'yes']

        club_member.approved = approved_status
        club_member.save()

        message = "Membership approved successfully." if approved_status else "Membership rejected."
        return Response({"message": message}, status=status.HTTP_200_OK)
    
    
    
#Event create view
class EventCreateView(generics.CreateAPIView):
    serializer_class = EventCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()
        
        
        
# Pending event list view
class PendingEventListView(generics.ListAPIView):
    serializer_class = PendingEventListSerializer
    permission_classes = [IsAuthenticated, IsModerator]

    def get_queryset(self):
        return Event.objects.filter(
            club__moderator=self.request.user,
            requires_approval=True,
            approved=False
        )


# pending event approval view
class EventApprovalView(generics.RetrieveUpdateAPIView):
    serializer_class = EventApprovalSerializer
    permission_classes = [IsModerator]
    lookup_field = 'id'

    def get_queryset(self):
        return Event.objects.filter(club__moderator=self.request.user)

    def update(self, request, *args, **kwargs):
        event = self.get_object()
        approved_status = request.data.get("approved", False)

        if approved_status is None:
            return Response(
                {"error": "Please provide 'approved' status (true/false)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if isinstance(approved_status, str):
            approved_status = approved_status.lower() in ['true', '1', 'yes']

        event.approved = approved_status
        event.requires_approval = False
        event.save()

        message = "Event approved successfully." if approved_status else "Event rejected."
        return Response({"message": message}, status=status.HTTP_200_OK)



# approve events list view
class ApprovedEventListView(generics.ListAPIView):
    serializer_class = ApprovedEventListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        now = timezone.now()
        return Event.objects.filter(
            approved=True,
            date_time__gt=now  # Only future events
        ).order_by('date_time')
        
        
# event list for moderator( only their club's approved events)
class ModeratorEventView(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView
):
    # moderators can view list of events they moderate, view single event detail, and delete an event
    serializer_class = ModeratorEventSerializer
    permission_classes = [IsAuthenticated, IsModerator]
    lookup_field = 'id'

    def get_queryset(self):
       # Return only approved events where this moderator is assigned
        return Event.objects.filter(
            club__moderator=self.request.user,
            approved=True
        )

    def get(self, request, *args, **kwargs):
        if 'id' in kwargs:
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        #Allow deletion only when event ID is provided.
        if 'id' not in kwargs:
            return Response(
                {"error": "You must specify an event ID to delete."},
                status=status.HTTP_400_BAD_REQUEST
            )

        event = self.get_object()
        event_name = event.title
        event.delete()
        return Response(
            {"message": f"Event '{event_name}' deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )
        
        
        
# Event registration view
class EventRegistrationFormView(generics.RetrieveUpdateAPIView):
    serializer_class = EventRegistrationFormSerializer
    permission_classes = [IsAuthenticated, IsStudent]
    lookup_field = 'id'

    def get_object(self):
        # The event itself is being displayed
        event = get_object_or_404(Event, id=self.kwargs['id'], approved=True)
        return event

    def get(self, request, *args, **kwargs):
        event = self.get_object()
        serializer = self.get_serializer(instance=EventRegistration(event=event))
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        event = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'request': request, 'event': event})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "You have successfully registered for this event."}, status=status.HTTP_201_CREATED)
    
    

# list of registration for an event
class EventRegistrationListByModeratorView(generics.ListAPIView):
    serializer_class = EventRegistrationListSerializer
    permission_classes = [IsAuthenticated, IsModerator]

    def get_queryset(self):
        user = self.request.user
        event_id = self.kwargs.get('event_id')

        # Get event
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise PermissionDenied("Event not found.")

        # Check if moderator is allowed to view
        if event.club.moderator != user:
            raise PermissionDenied("You are not authorized to view registrations for this event.")

        # Return list of registered users
        return EventRegistration.objects.filter(event=event)
    
    
# submit feedback view ( for registered students only)
class FeedbackCreateView(generics.CreateAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        return Feedback.objects.filter(registration__student=self.request.user)
    
 
# Feedback list view for moderators   
class EventFeedbackListView(generics.ListAPIView):
    
    # Feedback list view for moderators
    serializer_class = FeedbacklistSerializer
    permission_classes = [IsAuthenticated, IsModerator]

    def get_queryset(self):
        user = self.request.user
        event_id = self.kwargs.get('event_id')

        # Check if event exists and belongs to this moderator
        try:
            event = Event.objects.get(id=event_id, club__moderator=user)
        except Event.DoesNotExist:
            return Feedback.objects.none()  # Return empty if not their event

        # Fetch feedbacks related to this event
        return Feedback.objects.filter(registration__event=event).select_related(
            'registration__student',
            'registration__event__club'
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # If event doesn't belong to this moderator
        if not queryset.exists():
            return Response(
                {"detail": "No feedback found or you don't have permission for this event."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    
# Total number of registraions and amount collected for an event
class EventStatisticsView(generics.ListAPIView):
    serializer_class = EventStatisticsSerializer
    permission_classes = [IsAuthenticated, IsModerator]

    def get_queryset(self):
        user = self.request.user
        # Ensure only moderator’s club events are shown
        return (
            Event.objects.filter(club__moderator=user)
            .annotate(
                total_registrations=Count('registrations', distinct=True),
                total_amount_collected=ExpressionWrapper(
                    Count('registrations', distinct=True) * F('fee'),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            )
        )