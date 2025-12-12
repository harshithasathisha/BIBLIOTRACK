import re
import random
from datetime import datetime
from django.db.models import Q, Avg
from books.models import Book, Review
from recommendations.recommendation_engine import recommendation_engine
from .models import ChatSession, ChatMessage

class BiblioBot:
    def __init__(self):
        self.intents = {
            'greeting': {
                'patterns': [r'\b(hi|hello|hey|good morning|good afternoon|good evening)\b'],
                'responses': [
                    "Hello! I'm BiblioBot, your personal book assistant. How can I help you discover your next great read?",
                    "Hi there! I'm here to help you find amazing books. What are you in the mood for?",
                    "Greetings! I'm BiblioBot, ready to recommend some fantastic books. What interests you?"
                ]
            },
            'recommendation': {
                'patterns': [
                    r'\b(recommend|suggest|find me)\b.*\b(book|books|read|reading)\b',
                    r'\b(what should i read|what to read)\b',
                    r'\b(good books|best books)\b'
                ],
                'responses': [
                    "I'd be happy to recommend some books! Could you tell me what genres you enjoy or what you've read recently?",
                    "Great! I can help you find your next favorite book. What types of books interest you?",
                    "Perfect! Let me help you discover some amazing books. What genres or authors do you like?"
                ]
            },
            'genre_search': {
                'patterns': [
                    r'\b(fiction|non-fiction|mystery|romance|sci-fi|fantasy|biography|history|self-help|poetry)\b',
                    r'\b(science fiction|young adult|children|drama|horror|thriller|comedy|adventure)\b'
                ],
                'responses': [
                    "Excellent choice! I love {genre} books too. Let me find some great recommendations for you.",
                    "{genre} is such an interesting genre! Here are some wonderful books in that category.",
                    "Perfect! {genre} has so many amazing stories. Let me show you some top picks."
                ]
            },
            'author_search': {
                'patterns': [
                    r'\b(by|written by|author)\b.*\b([A-Z][a-z]+ [A-Z][a-z]+|[A-Z][a-z]+)\b',
                    r'\b(books by|works by)\b.*\b([A-Z][a-z]+ [A-Z][a-z]+|[A-Z][a-z]+)\b'
                ],
                'responses': [
                    "I see you're interested in books by {author}. Let me find their works in our catalog.",
                    "{author} is a wonderful author! Here are some of their books available.",
                    "Great choice! {author} has written some amazing books. Let me show you what's available."
                ]
            },
            'price_inquiry': {
                'patterns': [
                    r'\b(cheap|affordable|budget|inexpensive|low price)\b',
                    r'\b(expensive|costly|high price|premium)\b',
                    r'\b(how much|price|cost)\b'
                ],
                'responses': [
                    "I can help you find books within your budget! What price range are you looking for?",
                    "Price is important! Let me show you books in different price ranges. What's your budget?",
                    "I understand budget matters. Let me find some great books that fit your price range."
                ]
            },
            'rating_search': {
                'patterns': [
                    r'\b(high rated|best rated|top rated|highly rated)\b',
                    r'\b(rating|stars|review)\b.*\b(4|5|good|excellent|amazing)\b'
                ],
                'responses': [
                    "Looking for highly rated books? I can show you our top-rated selections!",
                    "Great choice! Let me find books with excellent ratings and reviews.",
                    "Perfect! I love recommending highly rated books. Here are some top picks."
                ]
            },
            'help': {
                'patterns': [
                    r'\b(help|what can you do|commands|features)\b',
                    r'\b(how to|how do i)\b'
                ],
                'responses': [
                    "I'm here to help you discover great books! I can:\n• Recommend books by genre or author\n• Find books within your budget\n• Show highly rated books\n• Help with book searches\n• Provide reading suggestions\n\nJust tell me what you're looking for!",
                    "I can assist you with:\n• Book recommendations by genre\n• Author searches\n• Price-based suggestions\n• Top-rated book lists\n• General reading advice\n\nWhat would you like to explore?",
                    "Here's what I can help you with:\n• Finding books in specific genres\n• Discovering new authors\n• Budget-friendly recommendations\n• Highly rated book suggestions\n• Answering book-related questions\n\nHow can I assist you today?"
                ]
            },
            'goodbye': {
                'patterns': [
                    r'\b(bye|goodbye|see you|thanks|thank you)\b',
                    r'\b(exit|quit|end|stop)\b'
                ],
                'responses': [
                    "Thank you for chatting with me! Happy reading! 📚",
                    "It was great helping you find some books! Enjoy your reading! 📖",
                    "Thanks for using BiblioBot! Come back anytime for more book recommendations! 📚"
                ]
            }
        }

    def classify_intent(self, message):
        """Classify user message intent using pattern matching"""
        message = message.lower().strip()

        for intent, data in self.intents.items():
            for pattern in data['patterns']:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    confidence = 0.8  # Simple confidence score
                    return intent, confidence, match.groups() if match.groups() else []

        return 'unknown', 0.0, []

    def generate_response(self, intent, confidence, groups, user, session):
        """Generate appropriate response based on intent"""
        if intent == 'unknown':
            return self._handle_unknown_intent()

        responses = self.intents[intent]['responses']
        response = random.choice(responses)

        # Handle specific intents with dynamic content
        if intent == 'genre_search' and groups:
            genre = groups[0].title()
            response = response.replace('{genre}', genre)
            # Add genre-specific book recommendations
            books = self._get_books_by_genre(genre.lower(), limit=3)
            if books:
                response += "\n\nHere are some great " + genre.lower() + " books:\n"
                for book in books:
                    response += f"• {book.title} by {book.author} (${book.price})\n"

        elif intent == 'author_search' and groups:
            author = groups[-1]  # Last captured group should be the author name
            response = response.replace('{author}', author)
            # Add author-specific recommendations
            books = self._get_books_by_author(author, limit=3)
            if books:
                response += "\n\nBooks by " + author + ":\n"
                for book in books:
                    response += f"• {book.title} (${book.price})\n"

        elif intent == 'recommendation':
            # Get personalized recommendations
            recs = recommendation_engine.generate_recommendations(user, top_k=3)
            if recs:
                response += "\n\nBased on your preferences, here are some recommendations:\n"
                for rec in recs:
                    book = rec['book']
                    response += f"• {book.title} by {book.author} - {rec['reason']} (${book.price})\n"

        elif intent == 'price_inquiry':
            # Show price ranges
            response += "\n\nOur books range from $5 to $50. Popular price ranges:\n• Budget: Under $15\n• Mid-range: $15-$30\n• Premium: Over $30\n\nWhat range interests you?"

        elif intent == 'rating_search':
            # Show top-rated books
            books = self._get_top_rated_books(limit=3)
            if books:
                response += "\n\nHere are our top-rated books:\n"
                for book in books:
                    response += f"• {book.title} by {book.author} ({book.average_rating}★, {book.total_ratings} reviews) - ${book.price}\n"

        return response

    def _handle_unknown_intent(self):
        """Handle unrecognized intents"""
        responses = [
            "I'm not sure I understand. Could you rephrase that? I can help with book recommendations, genre searches, or finding books by author.",
            "Hmm, I'm still learning! Try asking about specific genres, authors, or just say 'recommend books' for personalized suggestions.",
            "I didn't quite catch that. I specialize in book recommendations. Try asking about fiction, mystery, romance, or specific authors!",
            "Let me help you find some great books! What genre interests you, or do you have a favorite author?"
        ]
        return random.choice(responses)

    def _get_books_by_genre(self, genre, limit=5):
        """Get books by genre"""
        return Book.objects.filter(genre__iexact=genre)[:limit]

    def _get_books_by_author(self, author, limit=5):
        """Get books by author"""
        return Book.objects.filter(author__icontains=author)[:limit]

    def _get_top_rated_books(self, limit=5):
        """Get top-rated books"""
        return Book.objects.filter(average_rating__gte=4.0).order_by('-average_rating')[:limit]

    def process_message(self, message, user, session):
        """Process user message and return bot response"""
        # Classify intent
        intent, confidence, groups = self.classify_intent(message)

        # Generate response
        response = self.generate_response(intent, confidence, groups, user, session)

        # Save user message
        ChatMessage.objects.create(
            session=session,
            message_type='user',
            content=message,
            intent=intent,
            confidence=confidence
        )

        # Save bot response
        ChatMessage.objects.create(
            session=session,
            message_type='bot',
            content=response
        )

        return response

# Global chatbot instance
biblio_bot = BiblioBot()
