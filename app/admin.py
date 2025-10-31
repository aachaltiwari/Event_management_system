# from django.contrib import admin
# from .models import (
#     Role, User, StudentProfile,
#     Club, ClubMember, Event,
#     EventRegistration, Feedback
# )

# # ---------- ROLE ----------
# @admin.register(Role)
# class RoleAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name')
#     search_fields = ('name',)


# # ---------- USER ----------
# @admin.register(User)
# class UserAdmin(admin.ModelAdmin):
#     list_display = ('username', 'email', 'is_active', 'is_staff')
#     search_fields = ('username', 'email')
#     filter_horizontal = ('roles',)
#     fieldsets = (
#         (None, {'fields': ('username', 'email', 'password')}),
#         ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active', 'roles')}),
#     )
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('username', 'email', 'password1', 'password2', 'roles', 'is_active'),
#         }),
#     )

# admin.site.register(Role)
# admin.site.register(StudentProfile)


# # ---------- STUDENT PROFILE ----------
# @admin.register(StudentProfile)
# class StudentProfileAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'department', 'university_id')
#     search_fields = ('user__username', 'university_id', 'department')


# # ---------- CLUB ----------
# @admin.register(Club)
# class ClubAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name', 'moderator', 'status', 'created_by', 'created_at')
#     list_filter = ('status',)
#     search_fields = ('name', 'description')
#     readonly_fields = ('created_at',)


# # ---------- CLUB MEMBER ----------
# @admin.register(ClubMember)
# class ClubMemberAdmin(admin.ModelAdmin):
#     list_display = ('id', 'club', 'user', 'approved')
#     list_filter = ('approved', 'club')
#     search_fields = ('club__name', 'user__username')


# # ---------- EVENT ----------
# @admin.register(Event)
# class EventAdmin(admin.ModelAdmin):
#     list_display = ('id', 'title', 'club', 'venue', 'date_time', 'approved')
#     list_filter = ('approved', 'club')
#     search_fields = ('title', 'club__name', 'venue')
#     ordering = ('-date_time',)


# # ---------- EVENT REGISTRATION ----------
# @admin.register(EventRegistration)
# class EventRegistrationAdmin(admin.ModelAdmin):
#     list_display = ('id', 'event', 'student', 'registered_at', 'payment_done')
#     list_filter = ('payment_done', 'event')
#     search_fields = ('event__title', 'student__username')


# # ---------- FEEDBACK ----------
# @admin.register(Feedback)
# class FeedbackAdmin(admin.ModelAdmin):
#     list_display = ('id', 'get_event', 'get_student', 'rating')
#     list_filter = ('rating',)
#     search_fields = ('registration__event__title', 'registration__student__username')

#     def get_event(self, obj):
#         return obj.registration.event.title
#     get_event.short_description = 'Event'

#     def get_student(self, obj):
#         return obj.registration.student.username
#     get_student.short_description = 'Student'

