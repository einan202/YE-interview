from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from blog.models import Blog, Catagory, Comment, Tag
from .models import Author



class Dashboard(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        user = request.user
        author = getattr(user, 'author', None)
        if not author:
            messages.info(request, 'You need an author profile to use the dashboard.')
            return redirect('profile')
        post = author.blog_set.all()
        post_active = author.blog_set.filter(status='active')
        post_pending = author.blog_set.filter(status='pending')
        pending_comments_count = Comment.objects.filter(
            is_approved=False, post__author=author
        ).count()
        post_visit_count = post_active.aggregate(Sum('visit_count'))['visit_count__sum'] or 0
        context = {
            'user': user,
            'post': post,
            'post_count': post.count(),
            'post_active': post_active,
            'post_pending': post_pending,
            'post_active_count': post_active.count(),
            'post_pending_count': post_pending.count(),
            'pending_comments_count': pending_comments_count,
            'count': post_visit_count,
        }
        return render(request, 'dashboard/dash/dashboard.html', context)

# Create Author 
class CreateAuthor(View):
    def get(self,request,*args,**kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request,'dashboard/user/create_user.html')

    def post(self,request,*args,**kwargs):
        if request.method == 'POST':
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('fname')
            last_name = request.POST.get('lname')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            user = User.objects.filter(username=username)
            email_obj = Author.objects.filter(email=email)
            if user:
                messages.warning(request,'Username Already Exits!')
                return redirect ('create_user')
            elif password1 != password2:
                messages.warning(request,'Password Didn`t match')
                return redirect('create_user')
            else:
                auth_info={
                    'username':username,
                    'password':make_password(password1)
                }
                user = User(**auth_info)
                user.save()
            if email_obj:
                messages.warning(request,'Email Already Exits!')
                return redirect('create_user')
            else:
                user_other_obj = Author(author=user, email=email, first_name=first_name, last_name= last_name)
                user_other_obj.save(Author)
                messages.success(request,'Thanks for Joining Please Log in')
                return redirect('login')

# Author Profile (current logged-in user)
class AuthorProfile(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def get(self, request):
        user = request.user
        author = getattr(user, 'author', None)
        context = {
            'user': user,
            'author': author,
        }
        return render(request, 'dashboard/user/profile.html', context)

# Edit Author
class EditAuthor(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        author = getattr(request.user, 'author', None)
        context = {'user': request.user, 'author': author}
        return render(request, 'dashboard/user/edit_profile.html', context)

    def post(self, request):
        obj = getattr(request.user, 'author', None)
        if not obj:
            messages.error(request, 'You do not have an author profile to edit.')
            return redirect('profile')
        if request.FILES.get('image'):
            obj.author_image = request.FILES.get('image')
        obj.first_name = request.POST.get('fname') or obj.first_name
        obj.last_name = request.POST.get('lname') or obj.last_name
        obj.email = request.POST.get('email') or obj.email
        obj.save()
        messages.success(request, 'Your profile has been updated successfully.')
        return redirect('profile')


# Change password (current user)
class ChangePasswordView(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, 'dashboard/user/change_password.html')

    def post(self, request):
        user = request.user
        current = request.POST.get('current_password')
        new1 = request.POST.get('new_password1')
        new2 = request.POST.get('new_password2')
        if not user.check_password(current):
            messages.error(request, 'Current password is incorrect.')
            return redirect('change_password')
        if not new1 or len(new1) < 8:
            messages.error(request, 'New password must be at least 8 characters.')
            return redirect('change_password')
        if new1 != new2:
            messages.error(request, 'New password and confirmation do not match.')
            return redirect('change_password')
        user.set_password(new1)
        user.save()
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)
        messages.success(request, 'Your password has been changed.')
        return redirect('profile')


# login View
class LoginView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'dashboard/user/login.html')
    def post(self, request,*args,**kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.warning(request, 'username or password didn`t match')
            return redirect('login')

# Logout View
class LogoutView(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def get(self,request,*args,**kwargs):
        logout(request)
        return redirect('home')
    
# post listing View Active
class PostListingActive(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def get(self,request,*args,**kwargs):
        author = getattr(request.user, 'author', None)
        if not author:
            messages.info(request, 'You need an author profile to view your posts.')
            return redirect('profile')
        post_active = author.blog_set.filter(status='active').order_by('-id')
        context={
            'post_active':post_active
        }
        return render(request,'dashboard/post/post_listing_active.html',context)

# post listing View Pending
class PostListingPending(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)   
    
    def get(self,request,*args,**kwargs):
        user = request.user
        if user.is_staff or user.is_superuser:
            post_pending = Blog.objects.filter(status='pending').order_by('-id')
        else:
            author = getattr(user, 'author', None)
            if not author:
                messages.info(request, 'You need an author profile to view pending posts.')
                return redirect('profile')
            post_pending = author.blog_set.filter(status='pending').order_by('-id')
        context={
            'post_pending':post_pending
        }
        return render(request,'dashboard/post/post_listing_pending.html',context)     

# Category Views
class CatagoryFunction(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def get(self, request,*args,**kwargs):
        catagory_obj = Catagory.objects.all().order_by('-id')
        context ={
            'catagory':catagory_obj
        }
        return render(request,'dashboard/catagory/catagory.html', context)

# add category
class AddCatagory(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def get(self,request):
        return render(request,'dashboard/catagory/catagory.html')

    def post(self, request):
        if request.method == 'POST':
            from django.utils.text import slugify
            catagory = request.POST.get('catagory', '').strip()
            if not catagory:
                messages.warning(request, 'Category name is required.')
                return redirect('category')
            cat_obj = Catagory.objects.filter(name__iexact=catagory)
            if cat_obj.exists():
                messages.warning(request, 'Sorry, this category already exists.')
                return redirect('category')
            slug = slugify(catagory) or 'category'
            obj = Catagory.objects.create(name=catagory, slug=slug)
            messages.success(request, 'Category successfully added.')
            return redirect('category')

# Edit Category
class UpdateCategory(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def post(self,request, id):
        obj = get_object_or_404(Catagory, id=id)
        obj.name = request.POST.get('category')
        obj.save()
        return redirect('category')

# Delete Category
class DeleteCategory(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def post(self, request, id):
        obj = get_object_or_404(Catagory, id=id)
        obj.delete() 
        return redirect('category') 

# Tag functions
class TagFunction(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def get(self, request):
        tag_obj = Tag.objects.all().order_by('-id')
        context = {
            'tag':tag_obj
        }   
        return render (request,'dashboard/tag/tag.html', context)
        
# add Tags
class AddTag(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def get(self,request):
        return render(request,'dashboard/tag/tag.html')

    def post(self,request):
        if request.method == 'POST':
            tag= request.POST.get('tag')
            obj = Tag.objects.create(name=tag)
            obj.save()
            return redirect('tag')

# update Tags
class UpdateTag(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def post(self,request, id):
        obj = get_object_or_404(Tag, id=id)
        obj.name = request.POST.get('tag')
        obj.save()
        return redirect('tag')

# Delete Tags
class DeleteTag(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def post(self, request, id):
        obj = get_object_or_404(Tag, id=id)
        obj.delete() 
        return redirect('tag') 

# Comment moderation
class PendingCommentsView(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_staff or user.is_superuser:
            comments = Comment.objects.filter(is_approved=False).select_related("post", "post__author")
        else:
            author = getattr(user, 'author', None)
            if not author:
                messages.info(request, 'You need an author profile to moderate comments.')
                return redirect('profile')
            comments = Comment.objects.filter(
                is_approved=False,
                post__author=author
            ).select_related("post", "post__author")

        context = {
            "comments": comments
        }
        return render(request, "dashboard/comments/comments_pending.html", context)


class ApproveCommentView(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def post(self, request, id, *args, **kwargs):
        comment = get_object_or_404(Comment, id=id)
        user = request.user
        author = getattr(user, 'author', None)
        if not (user.is_staff or user.is_superuser or (author and comment.post.author == author)):
            messages.error(request, "You do not have permission to approve this comment.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        comment.is_approved = True
        comment.save()
        messages.success(request, "Comment approved.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class DeleteCommentView(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def post(self, request, id, *args, **kwargs):
        comment = get_object_or_404(Comment, id=id)
        user = request.user
        author = getattr(user, 'author', None)
        if not (user.is_staff or user.is_superuser or (author and comment.post.author == author)):
            messages.error(request, "You do not have permission to delete this comment.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        comment.delete()
        messages.success(request, "Comment deleted.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# Post Lists 
# Create Post
class CreatePost(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)
    
    def get(self,request):
        if not getattr(request.user, 'author', None):
            messages.info(request, 'You need an author profile to create posts.')
            return redirect('profile')
        category = Catagory.objects.all()
        context = {
            'category': category
        }
        return render(request,'dashboard/post/create_post.html', context)

    def post(self, request):
        author = getattr(request.user, 'author', None)
        if not author:
            messages.error(request, 'You need an author profile to create posts.')
            return redirect('profile')
        title = request.POST.get('title', '').strip()
        detail = request.POST.get('detail', '').strip()
        image = request.FILES.get('image')
        category_id = request.POST.get('category', '').strip()
        status_action = request.POST.get('status_action', 'draft')
        if status_action == 'pending':
            post_status = 'pending'
        else:
            post_status = 'draft'

        if not category_id:
            messages.error(request, 'Please select a category. Posts must have a category to be saved.')
            category = Catagory.objects.all()
            context = {'category': category, 'title': title, 'detail': detail}
            return render(request, 'dashboard/post/create_post.html', context)
        try:
            cat_obj = Catagory.objects.get(id=category_id)
        except (Catagory.DoesNotExist, ValueError):
            messages.error(request, 'Please select a valid category.')
            category = Catagory.objects.all()
            context = {'category': category, 'title': title, 'detail': detail}
            return render(request, 'dashboard/post/create_post.html', context)

        post_obj = Blog(author=author, title=title, detail=detail, image=image, catagories=cat_obj, status=post_status)
        post_obj.save()
        if post_status == 'draft':
            messages.success(
                request,
                'Post saved as draft. It will not appear on the main or category pages until you submit for review and a staff member publishes it.'
            )
        else:
            messages.success(
                request,
                'Post submitted for review. It will appear on the main and category pages after a staff member publishes it.'
            )
        return redirect('all_post')

# All Post show
class AllPost(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)
    
    def get(self,request):
        author = getattr(request.user, 'author', None)
        if not author:
            messages.info(request, 'You need an author profile to view your posts.')
            return redirect('profile')
        post = author.blog_set.annotate(
            likes_count=Count('likes', filter=~Q(likes__reaction='dislike'))
        ).order_by('-id')
        context = {
            'post':post
        }
        return render(request,'dashboard/post/all_post.html',context)

# Post detail 
class PostView(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self, request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)
    
    def get(self, request,id):
        post_obj = get_object_or_404(Blog, id=id)
        context={
            'post':post_obj
        }
        return render(request,'dashboard/post/post_view.html', context)


class SubmitPostForReview(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def post(self, request, id, *args, **kwargs):
        post = get_object_or_404(Blog, id=id)
        user = request.user
        author = getattr(user, 'author', None)
        if not (user.is_staff or user.is_superuser or (author and post.author == author)):
            messages.error(request, "You do not have permission to submit this post for review.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        post.status = 'pending'
        post.save()
        messages.success(request, "Post submitted for review.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class PublishPost(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def post(self, request, id, *args, **kwargs):
        post = get_object_or_404(Blog, id=id)
        user = request.user
        if not (user.is_staff or user.is_superuser):
            messages.error(request, "Only staff can publish posts.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        post.status = 'active'
        post.save()
        messages.success(request, "Post published.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class ReturnPostToDraft(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def post(self, request, id, *args, **kwargs):
        post = get_object_or_404(Blog, id=id)
        user = request.user
        if not (user.is_staff or user.is_superuser):
            messages.error(request, "Only staff can move posts back to draft.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        post.status = 'draft'
        post.save()
        messages.success(request, "Post moved back to draft.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class AnalyticsView(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        user = request.user
        author = getattr(user, 'author', None)
        if not author:
            messages.info(request, 'You need an author profile to view analytics.')
            return redirect('profile')
        # only this author's active (approved) posts; draft/pending do not show views/likes
        posts = Blog.objects.filter(author=author, status='active').annotate(
            likes_count=Count('likes', filter=~Q(likes__reaction='dislike'))
        ).order_by('-visit_count')

        # range: 1, 3, or 7 days (from ?range=1|3|7)
        range_param = request.GET.get('range', '7')
        if range_param not in ('1', '3', '7'):
            range_param = '7'
        num_days = int(range_param)
        range_label = {'1': 'Today', '3': 'Last 3 days', '7': 'Last 7 days'}.get(range_param, 'Last 7 days')

        # build per-post views + reaction breakdown
        today = timezone.now().date()
        posts_data = []
        for post in posts:
            days = []
            max_views = 0
            for i in range(num_days - 1, -1, -1):
                day = today - timedelta(days=i)
                pv = post.daily_views.filter(date=day).first()
                views = pv.views if pv else 0
                days.append({'date': day, 'views': views})
                if views > max_views:
                    max_views = views
            period_total = sum(d['views'] for d in days)
            for d in days:
                if max_views > 0:
                    d['height'] = int((d['views'] / float(max_views)) * 100)
                else:
                    d['height'] = 0

            # reaction breakdown per post
            reactions_qs = post.likes.values('reaction').annotate(c=Count('id'))
            reaction_counts = {
                'like': 0,
                'love': 0,
                'clap': 0,
                'insightful': 0,
                'dislike': 0,
            }
            for row in reactions_qs:
                key = row['reaction']
                if key in reaction_counts:
                    reaction_counts[key] = row['c']

            posts_data.append({
                'post': post,
                'chart_days': days,
                'period_total': period_total,
                'reaction_counts': reaction_counts,
            })

        totals = posts.aggregate(
            total_views=Sum('visit_count'),
            total_likes=Sum('likes_count'),
        )

        context = {
            "posts": posts,
            "posts_data": posts_data,
            "total_views": totals.get("total_views") or 0,
            "total_likes": totals.get("total_likes") or 0,
            "range_param": range_param,
            "range_label": range_label,
        }
        if request.GET.get("partial") or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return render(request, "dashboard/analytics_partial.html", context)
        return render(request, "dashboard/analytics.html", context)
    
        
# Edit Post
class EditPost(View):
    @method_decorator(login_required(login_url='login'))   
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)

    def get(self, request, id):
        obj = get_object_or_404(Blog, id=id)
        author = getattr(request.user, 'author', None)
        if not (request.user.is_staff or request.user.is_superuser or (author and obj.author == author)):
            messages.error(request, "You do not have permission to edit this post.")
            return redirect('all_post')
        cat_obj = Catagory.objects.all()
        context = {
            'obj': obj,
            'cat': cat_obj
        }
        return render(request, 'dashboard/post/edit_post.html', context)

    def post(self, request, id):
        obj = get_object_or_404(Blog, id=id)
        author = getattr(request.user, 'author', None)
        if not (request.user.is_staff or request.user.is_superuser or (author and obj.author == author)):
            messages.error(request, "You do not have permission to edit this post.")
            return redirect('all_post')
        obj.title = request.POST.get('title')
        obj.detail = request.POST.get('detail')
        if request.FILES.get('image'):
            obj.image = request.FILES.get('image')
        category = request.POST.get('category')
        if category:
            obj.catagories = Catagory.objects.get(name=category)
        obj.save()
        messages.success(request, 'Post has been Updated')
        return redirect('all_post')

# Make VIsible
class VisiblePost(View):
    @method_decorator(login_required(login_url='login'))   
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)
    
    def get(self,request,id):
        obj  = Blog.objects.get(id=id)
        obj.visible = True
        obj.save()
        messages.success(request,'Post is Visible')
        # Redirect To the Same Page
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# Make Hidden
class HidePost(View):
    @method_decorator(login_required(login_url='login'))   
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)
    
    def get(self,request,id):
        obj  = Blog.objects.get(id=id)
        obj.visible = False
        obj.save()
        messages.success(request,'Post is Hidden')

        # Redirect To the Same Page
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# Delete Posts
class DeletePost(View):
    @method_decorator(login_required(login_url='login'))
    def dispatch(self,request,*args,**kwargs):
        return super().dispatch(request,*args,**kwargs)
    

    def post(self, request,id):
        obj = get_object_or_404(Blog, id=id)
        obj.delete()
        messages.success(request,'Post Has Been Deleted')
        # Redirect To the Same Page
        return redirect('all_post')
