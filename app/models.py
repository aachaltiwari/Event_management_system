from django.contrib.auth.models import AbstractUser
from django.db import models


# Role model
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)   

    def __str__(self):
        return self.name


# user model
class User(AbstractUser):
    email = models.EmailField(unique=True)
    roles = models.ManyToManyField(Role, related_name='users')

    def has_role(self, role_name):
        return self.roles.filter(name=role_name).exists()


# student profile model
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    department = models.CharField(max_length=100)
    university_id = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.user.username} - Student"


# club model
class Club(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_clubs')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_clubs')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


#club member model
class ClubMember(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='club_memberships')
    approved = models.BooleanField(default=False)   # approved by moderator

    def __str__(self):
        return f"{self.user.username} in {self.club.name}"



# event model
class Event(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=150)
    description = models.TextField()
    date_time = models.DateTimeField()
    venue = models.CharField(max_length=150)
    max_participants = models.PositiveIntegerField()
    fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    requires_approval = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)  # moderator approval

    def __str__(self):
        return f"{self.title} ({self.club.name})"



# Event Registration model
class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    registered_at = models.DateTimeField(auto_now_add=True)
    payment_done = models.BooleanField(default=False)

    class Meta:
        unique_together = ('event', 'student')

    def __str__(self):
        return f"{self.student.username} registered for {self.event.title}"



# Feedback model
class Feedback(models.Model):
    registration = models.OneToOneField(EventRegistration, on_delete=models.CASCADE, related_name='feedback')
    rating = models.PositiveIntegerField(default=5)
    comments = models.TextField(blank=True)

    def __str__(self):
        return f"Feedback by {self.registration.student.username} for {self.registration.event.title}"