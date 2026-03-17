from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone

class Author(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    isbn = models.CharField(max_length=13, unique=True)
    published_date = models.DateField()
    copies_available = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='book_covers/', null=True, blank=True)

    def __str__(self):
        return self.title

class BorrowRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrow_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField(default=timezone.now() + timedelta(days=14))
    return_date = models.DateTimeField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    @property
    def status(self):
        if self.is_returned:
            return "Returned"
        if not self.is_approved:
            return "Pending"
        return "Borrowed"

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.status})"

    def save(self, *args, **kwargs):
        # Ensure book availability stays in sync when the borrow record state changes.
        if self.pk:
            previous = BorrowRecord.objects.select_related('book').get(pk=self.pk)

            # When a borrow is marked returned, restore one copy.
            if not previous.is_returned and self.is_returned:
                self.book.copies_available += 1
                self.book.save()

            # When a borrow is unmarked returned, consume one copy (if available).
            elif previous.is_returned and not self.is_returned:
                if self.book.copies_available > 0:
                    self.book.copies_available -= 1
                    self.book.save()

            # When approval flips, adjust copies accordingly (only if not already returned).
            if not previous.is_approved and self.is_approved and not self.is_returned:
                if self.book.copies_available > 0:
                    self.book.copies_available -= 1
                    self.book.save()
            elif previous.is_approved and not self.is_approved and not self.is_returned:
                self.book.copies_available += 1
                self.book.save()
        else:
            # New borrow record: if already approved, consume a copy right away.
            if self.is_approved and not self.is_returned and self.book.copies_available > 0:
                self.book.copies_available -= 1
                self.book.save()

        super().save(*args, **kwargs)

    def is_overdue(self):
        return not self.is_returned and timezone.now() > self.due_date
