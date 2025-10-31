from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import StudentRegistrationView, ModeratorRegistrationView, UserProfileView, ClubRequestView, ClubApprovalView, ModeratorClubView, ClubMemberApprovalView, StudentClubListView, ClubMembershipApplyView, ClubMemberRequestListView, EventCreateView, PendingEventListView, EventApprovalView, ApprovedEventListView, ModeratorEventView, EventRegistrationFormView, EventRegistrationListByModeratorView, FeedbackCreateView, EventFeedbackListView, EventStatisticsView


urlpatterns = [
    # User registration endpoints
    path('register/student/', StudentRegistrationView.as_view(), name='student-register'),
    path('register/moderator/', ModeratorRegistrationView.as_view(), name='moderator-register'),
    
    
    # JWT authentication endpoints, to obtain access and refresh tokens
    path('token/', TokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    
    # to get user profile details
    path('profile/', UserProfileView.as_view()),
    
    # to create new club 
    path('club/request/', ClubRequestView.as_view()),
    
    # to approve or reject created club 
    path('club/approve/', ClubApprovalView.as_view()),
    path('club/approve/<int:id>/', ClubApprovalView.as_view()),
    
    # to list all student clubs and apply for membership
    path('clubs/', StudentClubListView.as_view()),
    path('clubs/<int:club_id>/apply/', ClubMembershipApplyView.as_view(), name='apply-club'),
    
    
    # to list all membership requests  and approve or reject membership requests
    path('club/member/request/', ClubMemberRequestListView.as_view()),
    path('club/member/approve/<int:id>/', ClubMemberApprovalView.as_view()),
    
    # moderaotor's club list
    path('moderator/clubs/', ModeratorClubView.as_view(), name='moderator-club-list'),
    path('moderator/clubs/<int:id>/', ModeratorClubView.as_view(), name='moderator-club-detail'),
    
    # event creation, pending event list and approval of pending events
    path('event/create/', EventCreateView.as_view()),
    path('event/pending/', PendingEventListView.as_view()), 
    path('event/approve/<int:id>/', EventApprovalView.as_view()),
    
    
    # approved events list for students and event registration
    path('event/approved/', ApprovedEventListView.as_view()),
    path('event/register/<int:id>', EventRegistrationFormView.as_view(), name = 'event-register-form'),
    
    #event list ( which are moderated by the logged in moderator ) 
    path('moderator/events/', ModeratorEventView.as_view(), name='moderator-events-list'),
    path('moderator/events/<int:id>/', ModeratorEventView.as_view(), name='moderator-event-detail'),
    
    #registration list for an event
    path('event/registrations/<int:event_id>/', EventRegistrationListByModeratorView.as_view(), name='event-registrations'),
    
    # feedback submission
    path('feedback/', FeedbackCreateView.as_view(), name='event-feedback'),
    path('event/<int:event_id>/feedbacks/', EventFeedbackListView.as_view(), name='event-feedback-list'),
    
    # event statistics for moderators
    path('event/statistics/', EventStatisticsView.as_view(), name='event-statistics'),
     
     
]