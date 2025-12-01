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

    def __str__(self):
        return self.title

class BorrowRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrow_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField(default=timezone.now() + timedelta(days=14))
    return_date = models.DateTimeField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

    def is_overdue(self):
        return not self.is_returned and timezone.now() > self.due_date
