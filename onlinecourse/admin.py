from django.contrib import admin
from .models import Course, Lesson, Instructor, Learner, Enrollment, Question, Choice

# ChoiceInline — shows Choices nested inside the Question form
class ChoiceInline(admin.StackedInline):
    model = Choice
    extra = 3  # show 3 empty choice slots by default

# QuestionInline — shows Questions nested inside the Course form
class QuestionInline(admin.StackedInline):
    model = Question
    extra = 3  # show 3 empty question slots by default

# QuestionAdmin — how Questions appear on their own admin page
class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]  # when editing a Question, show its Choices inline

# LessonInline — shows Lessons nested inside the Course form
class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 5

# CourseAdmin — the main Course admin with Questions and Lessons inline
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline, QuestionInline]

# LessonAdmin — how Lessons appear on their own page
class LessonAdmin(admin.ModelAdmin):
    pass

# Register everything
admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Instructor)
admin.site.register(Learner)
admin.site.register(Enrollment)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)