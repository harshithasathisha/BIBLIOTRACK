from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Count
from .models import BookClub, Message, Comment, Like, Reply, Notification
from books.models import Book

@login_required
def book_club_chat(request, book_id):
    """Display chat interface for a book club"""
    book = get_object_or_404(Book, pk=book_id)

    # Get or create book club
    book_club, created = BookClub.objects.get_or_create(
        book=book,
        defaults={'is_active': True}
    )

    # Get recent messages
    messages = Message.objects.filter(book_club=book_club)\
        .select_related('user')\
        .order_by('-timestamp')[:50]  # Last 50 messages

    # Reverse to show chronological order
    messages = reversed(messages)

    context = {
        'book': book,
        'book_club': book_club,
        'messages': messages,
    }
    return render(request, 'chat/book_club.html', context)

@require_POST
@login_required
def send_message(request, book_id):
    """Send a message via AJAX"""
    book = get_object_or_404(Book, pk=book_id)
    book_club = get_object_or_404(BookClub, book=book)

    content = request.POST.get('content', '').strip()
    if content:
        Message.objects.create(
            book_club=book_club,
            user=request.user,
            content=content
        )
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Message cannot be empty'})

@login_required
def get_messages(request, book_id):
    """Get recent messages via AJAX"""
    book = get_object_or_404(Book, pk=book_id)
    book_club = get_object_or_404(BookClub, book=book)

    # Get messages after a certain timestamp if provided
    after_timestamp = request.GET.get('after')
    messages_query = Message.objects.filter(book_club=book_club).select_related('user')

    if after_timestamp:
        from django.utils.dateparse import parse_datetime
        after_dt = parse_datetime(after_timestamp)
        if after_dt:
            messages_query = messages_query.filter(timestamp__gt=after_dt)

    messages = messages_query.order_by('timestamp')[:100]  # Limit to prevent overload

    message_data = [{
        'id': msg.id,
        'user': msg.user.username,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat()
    } for msg in messages]

    return JsonResponse({'messages': message_data})

@login_required
def book_comments(request, book_id):
    """Display comments for a book"""
    book = get_object_or_404(Book, pk=book_id)
    comments = Comment.objects.filter(book=book)\
        .select_related('user')\
        .prefetch_related('likes', 'replies__user')\
        .annotate(like_count=Count('likes'))\
        .order_by('-created_at')

    context = {
        'book': book,
        'comments': comments,
    }
    return render(request, 'books/book_comments.html', context)

@require_POST
@login_required
def add_comment(request, book_id):
    """Add a comment to a book"""
    book = get_object_or_404(Book, pk=book_id)
    content = request.POST.get('content', '').strip()

    if content:
        comment = Comment.objects.create(
            book=book,
            user=request.user,
            content=content
        )

        # Create notification for other users who commented on this book
        other_commenters = Comment.objects.filter(book=book)\
            .exclude(user=request.user)\
            .values_list('user', flat=True)\
            .distinct()

        for commenter_id in other_commenters:
            Notification.objects.create(
                user_id=commenter_id,
                notification_type='comment',
                title='New Comment',
                message=f'{request.user.username} commented on "{book.title}"',
                related_object_id=comment.id,
                related_object_type='comment'
            )

        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'user': comment.user.username,
                'content': comment.content,
                'created_at': comment.created_at.isoformat(),
                'likes_count': 0,
                'replies_count': 0
            }
        })

    return JsonResponse({'success': False, 'error': 'Comment cannot be empty'})

@require_POST
@login_required
def like_comment(request, comment_id):
    """Like or unlike a comment"""
    comment = get_object_or_404(Comment, pk=comment_id)
    like, created = Like.objects.get_or_create(
        comment=comment,
        user=request.user
    )

    if not created:
        # Unlike
        like.delete()
        comment.likes_count = max(0, comment.likes_count - 1)
        liked = False
    else:
        # Like
        comment.likes_count += 1
        liked = True

        # Create notification if liking someone else's comment
        if comment.user != request.user:
            Notification.objects.create(
                user=comment.user,
                notification_type='like',
                title='Comment Liked',
                message=f'{request.user.username} liked your comment on "{comment.book.title}"',
                related_object_id=comment.id,
                related_object_type='comment'
            )

    comment.save()

    return JsonResponse({
        'success': True,
        'liked': liked,
        'likes_count': comment.likes_count
    })

@require_POST
@login_required
def reply_to_comment(request, comment_id):
    """Reply to a comment"""
    comment = get_object_or_404(Comment, pk=comment_id)
    content = request.POST.get('content', '').strip()

    if content:
        reply = Reply.objects.create(
            comment=comment,
            user=request.user,
            content=content
        )

        comment.replies_count += 1
        comment.save()

        # Create notification for comment author
        if comment.user != request.user:
            Notification.objects.create(
                user=comment.user,
                notification_type='reply',
                title='New Reply',
                message=f'{request.user.username} replied to your comment on "{comment.book.title}"',
                related_object_id=reply.id,
                related_object_type='reply'
            )

        return JsonResponse({
            'success': True,
            'reply': {
                'id': reply.id,
                'user': reply.user.username,
                'content': reply.content,
                'created_at': reply.created_at.isoformat()
            }
        })

    return JsonResponse({'success': False, 'error': 'Reply cannot be empty'})
