import os
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from faker import Faker
from books.models import Book

class Command(BaseCommand):
    help = 'Populate the database with 100 sample books'

    def handle(self, *args, **options):
        fake = Faker()

        # List of genres
        genres = [
            'fiction', 'non-fiction', 'mystery', 'romance', 'sci-fi',
            'fantasy', 'biography', 'history', 'self-help', 'poetry',
            'drama', 'horror', 'thriller', 'comedy', 'adventure',
            'children', 'young-adult', 'other'
        ]

        # List of sample book titles and authors
        sample_books = [
            ('The Great Gatsby', 'F. Scott Fitzgerald', 'fiction'),
            ('To Kill a Mockingbird', 'Harper Lee', 'fiction'),
            ('1984', 'George Orwell', 'sci-fi'),
            ('Pride and Prejudice', 'Jane Austen', 'romance'),
            ('The Catcher in the Rye', 'J.D. Salinger', 'fiction'),
            ('Harry Potter and the Philosopher\'s Stone', 'J.K. Rowling', 'fantasy'),
            ('The Lord of the Rings', 'J.R.R. Tolkien', 'fantasy'),
            ('The Hobbit', 'J.R.R. Tolkien', 'fantasy'),
            ('Dune', 'Frank Herbert', 'sci-fi'),
            ('Neuromancer', 'William Gibson', 'sci-fi'),
            ('The Name of the Wind', 'Patrick Rothfuss', 'fantasy'),
            ('Mistborn: The Final Empire', 'Brandon Sanderson', 'fantasy'),
            ('The Way of Kings', 'Brandon Sanderson', 'fantasy'),
            ('The Lies of Locke Lamora', 'Scott Lynch', 'fantasy'),
            ('American Gods', 'Neil Gaiman', 'fantasy'),
            ('Good Omens', 'Neil Gaiman & Terry Pratchett', 'fantasy'),
            ('The Night Circus', 'Erin Morgenstern', 'fantasy'),
            ('Jonathan Strange & Mr Norrell', 'Susanna Clarke', 'fantasy'),
            ('The Ocean at the End of the Lane', 'Neil Gaiman', 'fantasy'),
            ('Stardust', 'Neil Gaiman', 'fantasy'),
            ('The Graveyard Book', 'Neil Gaiman', 'children'),
            ('Coraline', 'Neil Gaiman', 'children'),
            ('Neverwhere', 'Neil Gaiman', 'fantasy'),
            ('Sandman: Preludes & Nocturnes', 'Neil Gaiman', 'fantasy'),
            ('The Sandman: The Doll\'s House', 'Neil Gaiman', 'fantasy'),
            ('The Sandman: Dream Country', 'Neil Gaiman', 'fantasy'),
            ('The Sandman: Season of Mists', 'Neil Gaiman', 'fantasy'),
            ('The Sandman: A Game of You', 'Neil Gaiman', 'fantasy'),
            ('The Sandman: Fables & Reflections', 'Neil Gaiman', 'fantasy'),
            ('The Sandman: Brief Lives', 'Neil Gaiman', 'fantasy'),
            ('The Sandman: Worlds\' End', 'Neil Gaiman', 'fantasy'),
            ('The Sandman: The Kindly Ones', 'Neil Gaiman', 'fantasy'),
            ('The Sandman: The Wake', 'Neil Gaiman', 'fantasy'),
            ('The Princess Bride', 'William Goldman', 'fantasy'),
            ('Watership Down', 'Richard Adams', 'fantasy'),
            ('The Earthsea Cycle', 'Ursula K. Le Guin', 'fantasy'),
            ('A Wizard of Earthsea', 'Ursula K. Le Guin', 'fantasy'),
            ('The Left Hand of Darkness', 'Ursula K. Le Guin', 'sci-fi'),
            ('The Dispossessed', 'Ursula K. Le Guin', 'sci-fi'),
            ('The Ones Who Walk Away from Omelas', 'Ursula K. Le Guin', 'sci-fi'),
            ('The Left Hand of Darkness', 'Ursula K. Le Guin', 'sci-fi'),
            ('The Farthest Shore', 'Ursula K. Le Guin', 'fantasy'),
            ('Tehanu', 'Ursula K. Le Guin', 'fantasy'),
            ('Tales from Earthsea', 'Ursula K. Le Guin', 'fantasy'),
            ('The Other Wind', 'Ursula K. Le Guin', 'fantasy'),
            ('The Stone Boatmen', 'Sarah Tolmie', 'fantasy'),
            ('The Winged Histories', 'Sofia Samatar', 'fantasy'),
            ('A Stranger in Olondria', 'Sofia Samatar', 'fantasy'),
            ('Kalane\'s Grace', 'Sofia Samatar', 'fantasy'),
            ('The Winged Histories', 'Sofia Samatar', 'fantasy'),
            ('The Gilded Ones', 'Namina Forna', 'young-adult'),
            ('The Gilded Ones', 'Namina Forna', 'young-adult'),
            ('The Conductors', 'Nicole Glover', 'fantasy'),
            ('The Conductors', 'Nicole Glover', 'fantasy'),
            ('The Year of the Witching', 'Alexis Henderson', 'fantasy'),
            ('The Year of the Witching', 'Alexis Henderson', 'fantasy'),
            ('The Invisible Life of Addie LaRue', 'V.E. Schwab', 'fantasy'),
            ('The Invisible Life of Addie LaRue', 'V.E. Schwab', 'fantasy'),
            ('City of Brass', 'S.A. Chakraborty', 'fantasy'),
            ('The Kingdom of Copper', 'S.A. Chakraborty', 'fantasy'),
            ('The Empire of Gold', 'S.A. Chakraborty', 'fantasy'),
            ('The Jasmine Throne', 'Tasha Suri', 'fantasy'),
            ('Empire of Sand', 'Tasha Suri', 'fantasy'),
            ('The Jasmine Throne', 'Tasha Suri', 'fantasy'),
            ('The Unspoken Name', 'A.K. Larkwood', 'fantasy'),
            ('The Thousand Eyes', 'A.K. Larkwood', 'fantasy'),
            ('The Unbroken', 'C.L. Clark', 'fantasy'),
            ('The Unspoken Name', 'A.K. Larkwood', 'fantasy'),
            ('The Thousand Eyes', 'A.K. Larkwood', 'fantasy'),
            ('The Unbroken', 'C.L. Clark', 'fantasy'),
            ('The Black Sun', 'Rebecca Roanhorse', 'fantasy'),
            ('Trail of Lightning', 'Rebecca Roanhorse', 'fantasy'),
            ('Black Sun', 'Rebecca Roanhorse', 'fantasy'),
            ('The Black God\'s Drums', 'P. Djèlí Clark', 'fantasy'),
            ('Ring Shout', 'P. Djèlí Clark', 'horror'),
            ('The Haunting of Tram Car 015', 'P. Djèlí Clark', 'horror'),
            ('The Empress of Salt and Fortune', 'Nghi Vo', 'fantasy'),
            ('Siren Queen', 'Nghi Vo', 'fantasy'),
            ('The Empress of Salt and Fortune', 'Nghi Vo', 'fantasy'),
            ('When the Tiger Came Down the Mountain', 'Nghi Vo', 'fantasy'),
            ('Into the Riverlands', 'Nghi Vo', 'fantasy'),
            ('The Chosen and the Beautiful', 'Nghi Vo', 'fantasy'),
            ('The Empress of Salt and Fortune', 'Nghi Vo', 'fantasy'),
            ('When the Tiger Came Down the Mountain', 'Nghi Vo', 'fantasy'),
            ('Into the Riverlands', 'Nghi Vo', 'fantasy'),
            ('The Chosen and the Beautiful', 'Nghi Vo', 'fantasy'),
            ('The Once and Future Witches', 'Alix E. Harrow', 'fantasy'),
            ('The Ten Thousand Doors of January', 'Alix E. Harrow', 'fantasy'),
            ('The Once and Future Witches', 'Alix E. Harrow', 'fantasy'),
            ('The Ten Thousand Doors of January', 'Alix E. Harrow', 'fantasy'),
            ('Mexican Gothic', 'Silvia Moreno-Garcia', 'horror'),
            ('The Year of the Witching', 'Alexis Henderson', 'fantasy'),
            ('The Invisible Life of Addie LaRue', 'V.E. Schwab', 'fantasy'),
            ('City of Brass', 'S.A. Chakraborty', 'fantasy'),
            ('The Jasmine Throne', 'Tasha Suri', 'fantasy'),
            ('The Unspoken Name', 'A.K. Larkwood', 'fantasy'),
            ('The Black Sun', 'Rebecca Roanhorse', 'fantasy'),
            ('The Black God\'s Drums', 'P. Djèlí Clark', 'fantasy'),
            ('The Empress of Salt and Fortune', 'Nghi Vo', 'fantasy'),
            ('The Once and Future Witches', 'Alix E. Harrow', 'fantasy'),
            ('Mexican Gothic', 'Silvia Moreno-Garcia', 'horror'),
            ('The House in the Cerulean Sea', 'TJ Klune', 'fantasy'),
            ('The Long Way to a Small, Angry Planet', 'Becky Chambers', 'sci-fi'),
            ('A Memory Called Empire', 'Arkady Martine', 'sci-fi'),
            ('A Desolation Called Peace', 'Arkady Martine', 'sci-fi'),
            ('The Network Effect', 'Martha Wells', 'sci-fi'),
            ('Exit Strategy', 'Martha Wells', 'sci-fi'),
            ('Network Effect', 'Martha Wells', 'sci-fi'),
            ('The Calculating Stars', 'Mary Robinette Kowal', 'sci-fi'),
            ('The Fated Sky', 'Mary Robinette Kowal', 'sci-fi'),
            ('The Relentless Moon', 'Mary Robinette Kowal', 'sci-fi'),
            ('The Calculating Stars', 'Mary Robinette Kowal', 'sci-fi'),
            ('The Fated Sky', 'Mary Robinette Kowal', 'sci-fi'),
            ('The Relentless Moon', 'Mary Robinette Kowal', 'sci-fi'),
            ('The Empress of Salt and Fortune', 'Nghi Vo', 'fantasy'),
            ('When the Tiger Came Down the Mountain', 'Nghi Vo', 'fantasy'),
            ('Into the Riverlands', 'Nghi Vo', 'fantasy'),
            ('The Chosen and the Beautiful', 'Nghi Vo', 'fantasy'),
            ('The Once and Future Witches', 'Alix E. Harrow', 'fantasy'),
            ('The Ten Thousand Doors of January', 'Alix E. Harrow', 'fantasy'),
            ('Mexican Gothic', 'Silvia Moreno-Garcia', 'horror'),
            ('The House in the Cerulean Sea', 'TJ Klune', 'fantasy'),
            ('The Long Way to a Small, Angry Planet', 'Becky Chambers', 'sci-fi'),
            ('A Memory Called Empire', 'Arkady Martine', 'sci-fi'),
            ('A Desolation Called Peace', 'Arkady Martine', 'sci-fi'),
            ('The Network Effect', 'Martha Wells', 'sci-fi'),
            ('Exit Strategy', 'Martha Wells', 'sci-fi'),
            ('Network Effect', 'Martha Wells', 'sci-fi'),
            ('The Calculating Stars', 'Mary Robinette Kowal', 'sci-fi'),
            ('The Fated Sky', 'Mary Robinette Kowal', 'sci-fi'),
            ('The Relentless Moon', 'Mary Robinette Kowal', 'sci-fi'),
            ('The Empress of Salt and Fortune', 'Nghi Vo', 'fantasy'),
            ('When the Tiger Came Down the Mountain', 'Nghi Vo', 'fantasy'),
            ('Into the Riverlands', 'Nghi Vo', 'fantasy'),
            ('The Chosen and the Beautiful', 'Nghi Vo', 'fantasy'),
            ('The Once and Future Witches', 'Alix E. Harrow', 'fantasy'),
            ('The Ten Thousand Doors of January', 'Alix E. Harrow', 'fantasy'),
            ('Mexican Gothic', 'Silvia Moreno-Garcia', 'horror'),
            ('The House in the Cerulean Sea', 'TJ Klune', 'fantasy'),
            ('The Long Way to a Small, Angry Planet', 'Becky Chambers', 'sci-fi'),
            ('A Memory Called Empire', 'Arkady Martine', 'sci-fi'),
            ('A Desolation Called Peace', 'Arkady Martine', 'sci-fi'),
            ('The Network Effect', 'Martha Wells', 'sci-fi'),
            ('Exit Strategy', 'Martha Wells', 'sci-fi'),
            ('Network Effect', 'Martha Wells', 'sci-fi'),
            ('The Calculating Stars', 'Mary Robinette Kowal', 'sci-fi'),
            ('The Fated Sky', 'Mary Robinette Kowal', 'sci-fi'),
            ('The Relentless Moon', 'Mary Robinette Kowal', 'sci-fi'),
        ]

        # Create books
        for i in range(100):
            if i < len(sample_books):
                title, author, genre = sample_books[i]
            else:
                title = fake.sentence(nb_words=4)[:-1]  # Remove the period
                author = fake.name()
                genre = fake.random_element(genres)

            # Generate random data
            isbn = fake.isbn13()
            description = fake.paragraph(nb_sentences=3)
            price = round(fake.random_number(digits=2) + fake.random_number(digits=1) / 10, 2)
            stock_quantity = fake.random_int(min=0, max=100)
            publication_date = fake.date_between(start_date='-50y', end_date='today')
            publisher = fake.company()
            page_count = fake.random_int(min=100, max=1000)
            language = fake.random_element(['English', 'Spanish', 'French', 'German', 'Italian'])
            average_rating = round(fake.random_number(digits=1) + fake.random_number(digits=1) / 10, 1)
            total_ratings = fake.random_int(min=0, max=1000)

            # Create book
            book = Book.objects.create(
                title=title,
                author=author,
                isbn=isbn,
                description=description,
                genre=genre,
                price=price,
                stock_quantity=stock_quantity,
                publication_date=publication_date,
                publisher=publisher,
                page_count=page_count,
                language=language,
                average_rating=average_rating,
                total_ratings=total_ratings,
            )

            # Try to download a cover image
            try:
                # Use Lorem Picsum for random images
                image_url = f'https://picsum.photos/300/400?random={i}'
                response = requests.get(image_url)
                if response.status_code == 200:
                    # Save the image
                    image_name = f'book_cover_{book.id}.jpg'
                    book.cover_image.save(image_name, ContentFile(response.content), save=True)
                    self.stdout.write(f'Successfully downloaded cover for "{title}"')
                else:
                    self.stdout.write(f'Failed to download cover for "{title}"')
            except Exception as e:
                self.stdout.write(f'Error downloading cover for "{title}": {e}')

            self.stdout.write(f'Created book: {title} by {author}')

        self.stdout.write(self.style.SUCCESS('Successfully populated 100 books'))
