
import uuid
from django.conf import settings
from django.db import models
from django.utils.text import slugify
from dashboard.models import Author


# Catagory model
class Catagory(models.Model):
    name = models.CharField(max_length=200, null=True)
    slug = models.SlugField(null=True, blank=True)
    image = models.CharField(max_length=300, null=True, blank=True)
    description = models.CharField(max_length=500, null=True, blank=True, verbose_name='Description')

    class Meta:
        verbose_name_plural = 'Catagory'

    def save(self, *args, **kwargs):
        if self.name and not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.name) 

# tags model
class Tag(models.Model):

    name  = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.name 

# Blog model 
class Blog(models.Model):
    STATUS_CHOICES = (
        ('draft', 'draft'),
        ('pending', 'pending'),
        ('active', 'active'),
    )

    title = models.CharField(max_length=200, null=True)
    detail = models.TextField(max_length=2000, null=True)
    image = models.ImageField(upload_to='images/media', null=True, blank=True)
    catagories = models.ForeignKey(Catagory, on_delete=models.DO_NOTHING, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    #show_hide = models.CharField(max_length=5,choices=visibility, default='show')
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    featured  = models.BooleanField(default=False)
    visit_count = models.IntegerField(default=0)
    visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Blog'

    def overview(self):
        return (self.detail or '')[:30]

    @property
    def image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return None

    @property
    def views_last_7_days(self):
        today = timezone.now().date()
        start_date = today - timedelta(days=6)
        result = self.daily_views.filter(
            date__gte=start_date, date__lte=today
        ).aggregate(total=Sum('views'))['total']
        return result or 0

    def __str__(self):
        return f"{self.title} | {self.author.author.username} | {self.catagories} | {self.status}"

class Comment(models.Model):
    post = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=100, null=True, blank=False)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.post.title} | {self.name}"


class Reply(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reply')
    name = models.CharField(max_length=200, null=True, blank=False)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.comment} | { self.name } |{ self.created_at }"


# email marketing system 
class EmailSignUp(models.Model):
    email  = models.EmailField(blank=True)

    class Meta:
        verbose_name_plural = " User Emails"

    def __str__(self):
        return self.email

class Contact(models.Model):
    name = models.CharField(max_length=100, null=True, verbose_name='Name')
    email = models.EmailField(null=True)
    messages = models.TextField()
    subject = models.CharField(max_length=200, null=True, verbose_name='Subjects')

    def __str__(self):
        return f"{self.name} | {self.subject}" 

class Like(models.Model):
    REACTION_CHOICES = (
        ('like', 'like'),
        ('love', 'love'),
        ('clap', 'clap'),
        ('insightful', 'insightful'),
        ('dislike', 'dislike'),
    )

    post = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='likes')
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    reaction = models.CharField(max_length=20, choices=REACTION_CHOICES, default='like')

    class Meta:
        unique_together = ('post', 'author')


class PostView(models.Model):
    post = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='daily_views')
    date = models.DateField()
    views = models.IntegerField(default=0)

    class Meta:
        unique_together = ('post', 'date')
        ordering = ['-date']


class PostFirstView(models.Model):
    """Tracks that a user has already been counted as a viewer for a post (one view per user per post)."""
    post = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='first_views')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('post', 'user')

