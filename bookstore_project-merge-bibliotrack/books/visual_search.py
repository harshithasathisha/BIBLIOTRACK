import os
import numpy as np
import cv2
import tensorflow as tf
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.preprocessing import image
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from .models import Book
import logging

logger = logging.getLogger(__name__)

class VisualSearchEngine:
    def __init__(self):
        self.model = None
        self.feature_cache = {}
        self._load_model()

    def _load_model(self):
        """Load the pre-trained ResNet50 model for feature extraction"""
        try:
            # Load ResNet50 without the top classification layer
            base_model = ResNet50(weights='imagenet', include_top=False, pooling='avg')
            self.model = tf.keras.Model(inputs=base_model.input, outputs=base_model.output)
            logger.info("ResNet50 model loaded successfully for visual search")
        except Exception as e:
            logger.error(f"Failed to load ResNet50 model: {e}")
            self.model = None

    def extract_features(self, image_path):
        """Extract features from an image using ResNet50"""
        if not self.model:
            return None

        try:
            # Load and preprocess the image
            img = image.load_img(image_path, target_size=(224, 224))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)

            # Extract features
            features = self.model.predict(img_array, verbose=0)
            return features.flatten()
        except Exception as e:
            logger.error(f"Error extracting features from {image_path}: {e}")
            return None

    def preprocess_uploaded_image(self, uploaded_file):
        """Preprocess uploaded image for feature extraction"""
        try:
            # Save uploaded file temporarily
            temp_path = os.path.join(settings.MEDIA_ROOT, 'temp_search.jpg')
            with open(temp_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Extract features
            features = self.extract_features(temp_path)

            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

            return features
        except Exception as e:
            logger.error(f"Error preprocessing uploaded image: {e}")
            return None

    def find_similar_books(self, query_features, top_k=10):
        """Find books with similar visual features"""
        if query_features is None:
            return []

        similar_books = []
        books_with_images = Book.objects.exclude(cover_image='').exclude(cover_image__isnull=True)

        for book in books_with_images:
            try:
                image_path = os.path.join(settings.MEDIA_ROOT, str(book.cover_image))

                if not os.path.exists(image_path):
                    continue

                # Get cached features or extract new ones
                if book.id not in self.feature_cache:
                    self.feature_cache[book.id] = self.extract_features(image_path)

                book_features = self.feature_cache[book.id]
                if book_features is None:
                    continue

                # Calculate similarity
                similarity = cosine_similarity([query_features], [book_features])[0][0]
                similarity_percentage = similarity * 100

                if similarity_percentage > 20:  # Only include reasonably similar images
                    similar_books.append((book, similarity_percentage))

            except Exception as e:
                logger.error(f"Error processing book {book.id}: {e}")
                continue

        # Sort by similarity and return top_k
        similar_books.sort(key=lambda x: x[1], reverse=True)
        return similar_books[:top_k]

    def search_by_image(self, uploaded_file, top_k=10):
        """Main method to search books by uploaded image"""
        query_features = self.preprocess_uploaded_image(uploaded_file)
        if query_features is None:
            return []

        return self.find_similar_books(query_features, top_k)

# Global instance
visual_search_engine = VisualSearchEngine()
