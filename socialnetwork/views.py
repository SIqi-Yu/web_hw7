# socialnetwork/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_datetime
from .models import Comment
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import LoginForm, RegisterForm, ProfileForm, PostForm
from .models import Profile, Post


def home(request):
    """
    If user is logged in, show global stream; otherwise, show login page.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    return redirect('global')

@ensure_csrf_cookie
def login_action(request):
    """
    Render login page; if POST, attempt to authenticate.
    """
    context = {}
    if request.method == 'GET':
        form = LoginForm()
        context['form'] = form
        return render(request, 'socialnetwork/login.html', context)

    # POST
    form = LoginForm(request.POST)
    context['form'] = form
    if not form.is_valid():
        return render(request, 'socialnetwork/login.html', context)

    username = form.cleaned_data['username']
    password = form.cleaned_data['password']
    user = authenticate(username=username, password=password)
    if not user:
        context['error'] = 'Invalid username or password.'
        return render(request, 'socialnetwork/login.html', context)

    # Log in and redirect
    login(request, user)
    return redirect('global')


def logout_action(request):
    """
    Log out the user and redirect to the login page.
    """
    logout(request)
    previous_page = request.META.get('HTTP_REFERER', '/global')
    return redirect(previous_page)


def register_action(request):
    """
    Handle the register form – create a new user if everything checks out
    and then log them in automatically.
    """
    context = {}
    if request.method == 'GET':
        form = RegisterForm()
        context['form'] = form
        return render(request, 'socialnetwork/register.html', context)

    # POST
    form = RegisterForm(request.POST)
    context['form'] = form

    if not form.is_valid():
        return render(request, 'socialnetwork/register.html', context)

    # Create the user
    new_user = User.objects.create_user(
        username=form.cleaned_data['username'],
        password=form.cleaned_data['password'],
        email=form.cleaned_data['email'],
        first_name=form.cleaned_data['first_name'],
        last_name=form.cleaned_data['last_name'],
    )
    new_user.save()

    # Create a Profile for the new user
    Profile.objects.create(user=new_user)

    # Log in the new user and redirect to the global stream
    login(request, new_user)
    return redirect('global')

def global_stream(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=401)

    if request.method == 'POST':
        post_form = PostForm(request.POST)
        if post_form.is_valid():
            new_post = post_form.save(commit=False)
            new_post.user = request.user
            new_post.save()
        return redirect('global')  # 提交后重新加载

    else:
        post_form = PostForm()

    posts = Post.objects.all().order_by('-creation_time')
    context = {
        'posts': posts,
        'post_form': post_form,
    }
    return render(request, 'socialnetwork/global.html', context)


def follower_stream(request):
    """
    Show only the posts made by people whom the current user follows.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=401)

    # If the user just posted something, handle it (the user can post to follower feed, too)
    if request.method == 'POST' and 'posttext' in request.POST:
        post_form = PostForm(request.POST)
        if post_form.is_valid():
            new_post = post_form.save(commit=False)
            new_post.user = request.user
            new_post.creation_time = timezone.now()
            new_post.save()
        return redirect('follower')
    else:
        post_form = PostForm()

    # Ensure current user has a profile
    my_profile, created = Profile.objects.get_or_create(user=request.user)

    # Get all the profiles that I'm following
    following_profiles = my_profile.following.all()
    # Extract the User objects from those profiles
    following_users = [p.user for p in following_profiles]

    # Query for posts whose `user` is in the set of following_users
    posts = Post.objects.filter(user__in=following_users).order_by('-creation_time')

    context = {
        'posts': posts,
        'post_form': post_form,
    }
    return render(request, 'socialnetwork/follower.html', context)

def my_profile(request):
    """
    Display and edit the logged-in user's profile.
    """
    # Get or create profile for the current user
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=401)

    my_profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=my_profile)
        if form.is_valid():
            form.save()
            return redirect('my_profile')
    else:
        form = ProfileForm(instance=my_profile)

    following_profiles = my_profile.following.all()

    context = {
        'user_fullname': f'{request.user.first_name} {request.user.last_name}',
        'bio': my_profile.bio,
        'picture': my_profile.picture,  # might be empty
        'following': following_profiles,  # pass the actual Profile objects
        'form': form
    }
    return render(request, 'socialnetwork/my_profile.html', context)


def other_profile(request, user_id):
    """
    Display some other user’s profile, with follow/unfollow link.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=401)

    # Find that user or 404
    other_user = get_object_or_404(User, id=user_id)
    # Get or create their profile
    other_profile_obj, created = Profile.objects.get_or_create(user=other_user)

    # If we clicked "Follow" or "Unfollow", handle it
    my_profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        if 'follow' in request.POST:
            my_profile.following.add(other_profile_obj)
        elif 'unfollow' in request.POST:
            my_profile.following.remove(other_profile_obj)
        return redirect('other_profile',  user_id=user_id)

    # Determine if we are following this other user
    am_following = other_profile_obj in my_profile.following.all()

    context = {
        'other_user_id': other_user.id,
        'user_fullname': f'{other_user.first_name} {other_user.last_name}',
        'bio': other_profile_obj.bio,
        'picture': other_profile_obj.picture,
        'can_follow': not am_following and other_user != request.user,
        'can_unfollow': am_following and other_user != request.user,
        'other_username': other_user.username,
    }
    return render(request, 'socialnetwork/other_profile.html', context)


def get_global_stream_json(request):
    """
    Returns a JSON response with *all* posts and their comments.
    Format must include all data needed by the client JS.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=401)

    if request.method != 'GET':
        return JsonResponse({'error': 'GET request required'}, status=405)

    # Retrieve all posts, sorted newest-first
    posts = Post.objects.all().order_by('-creation_time')

    # Build a list of dictionaries to serialize as JSON
    posts_list = []
    for post in posts:
        # For each post, gather its comments (oldest first if you want chronological ascending)
        comments_qs = post.comments.all().order_by('-creation_time')
        comments_data = []
        for c in comments_qs:
            comments_data.append({
                'id': c.id,
                'user_id': c.user.id,
                'first_name': c.user.first_name,
                'last_name': c.user.last_name,
                'text': c.text,
                # Use isoformat so you can parse in JS
                'creation_time': c.creation_time.isoformat(),
            })

        posts_list.append({
            'id': post.id,
            'user_id': post.user.id,
            'first_name': post.user.first_name,
            'last_name': post.user.last_name,
            'text': post.text,
            'creation_time': post.creation_time.isoformat(),
            'comments': comments_data,
        })

    return JsonResponse({'posts': posts_list}, status=200)

def get_follower_stream_json(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=401)

    if request.method != 'GET':
        return JsonResponse({'error': 'GET request required'}, status=405)

    # Current user's profile
    my_profile = Profile.objects.get(user=request.user)
    # All the profiles they follow
    following_profiles = my_profile.following.all()
    # Extract the user objects
    following_users = [p.user for p in following_profiles]

    # Get posts from those users, sorted newest-first
    posts = Post.objects.filter(user__in=following_users).order_by('creation_time')

    posts_list = []
    for post in posts:
        comments_qs = post.comments.all().order_by('-creation_time')
        comments_data = []
        for c in comments_qs:
            comments_data.append({
                'id': c.id,
                'user_id': c.user.id,
                'first_name': c.user.first_name,
                'last_name': c.user.last_name,
                'text': c.text,
                'creation_time': c.creation_time.isoformat(),
            })
        posts_list.append({
            'id': post.id,
            'user_id': post.user.id,
            'first_name': post.user.first_name,
            'last_name': post.user.last_name,
            'text': post.text,
            'creation_time': post.creation_time.isoformat(),
            'comments': comments_data,
        })

    return JsonResponse({'posts': posts_list}, status=200)


def add_comment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=401)

    text = request.POST.get('comment_text')
    post_id_str = request.POST.get('post_id')


    if not text or not post_id_str:
        return JsonResponse({'error': 'Missing comment_text or post_id'}, status=400)

    try:
        post_id = int(post_id_str)
    except ValueError:
        return JsonResponse({'error': 'Invalid post_id'}, status=400)

    # Validate that the post exists
    try:
        post_obj = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Invalid post_id'}, status=400)

    # Create a new comment
    new_comment = Comment(user=request.user, post=post_obj, text=text)
    new_comment.save()

    # Return a success response containing the new comment data
    return JsonResponse({
        'comment': {
            'id': new_comment.id,
            'user_id': new_comment.user.id,
            'first_name': new_comment.user.first_name,
            'last_name': new_comment.user.last_name,
            'text': new_comment.text,
            'creation_time': new_comment.creation_time.isoformat(),
        }
    }, status=200)