from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import ChatSession, ChatMessage
from .chatbot_engine import biblio_bot

@login_required
def chatbot_view(request):
    """Display the chatbot interface"""
    # Get or create active chat session
    session, created = ChatSession.objects.get_or_create(
        user=request.user,
        is_active=True,
        defaults={'started_at': timezone.now()}
    )

    # Get recent messages (last 50)
    messages = ChatMessage.objects.filter(session=session).order_by('-timestamp')[:50]
    messages = reversed(messages)  # Show oldest first

    context = {
        'messages': messages,
        'session': session,
    }
    return render(request, 'chatbot/chatbot.html', context)

@require_POST
@login_required
def send_message(request):
    """Handle user message and return bot response"""
    try:
        user_message = request.POST.get('message', '').strip()

        if not user_message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)

        # Get or create active session
        session, created = ChatSession.objects.get_or_create(
            user=request.user,
            is_active=True,
            defaults={'started_at': timezone.now()}
        )

        # Update session activity
        session.last_activity = timezone.now()
        session.save()

        # Process message with chatbot
        bot_response = biblio_bot.process_message(user_message, request.user, session)

        return JsonResponse({
            'success': True,
            'user_message': user_message,
            'bot_response': bot_response,
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_messages(request):
    """Get recent messages for the chat session"""
    try:
        session = ChatSession.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if not session:
            return JsonResponse({'messages': []})

        # Get messages since last check
        last_timestamp = request.GET.get('since')
        messages_query = ChatMessage.objects.filter(session=session)

        if last_timestamp:
            messages_query = messages_query.filter(timestamp__gt=last_timestamp)

        messages = messages_query.order_by('timestamp')[:20]  # Limit to prevent overload

        message_data = []
        for msg in messages:
            message_data.append({
                'type': msg.message_type,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'intent': msg.intent,
                'confidence': msg.confidence
            })

        return JsonResponse({'messages': message_data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_POST
@login_required
def clear_chat(request):
    """Clear chat history for current session"""
    try:
        session = ChatSession.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if session:
            # Delete all messages in session
            ChatMessage.objects.filter(session=session).delete()

            # Reset session start time
            session.started_at = timezone.now()
            session.save()

        return JsonResponse({'success': True, 'message': 'Chat history cleared'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def chat_history(request):
    """View chat history across all sessions"""
    sessions = ChatSession.objects.filter(user=request.user).order_by('-last_activity')

    context = {
        'sessions': sessions,
    }
    return render(request, 'chatbot/chat_history.html', context)
