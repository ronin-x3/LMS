from django.contrib import admin
from .models import Author, Category, Book, BorrowRecord


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
	list_display = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
	list_display = ('title', 'author', 'category', 'copies_available')
	search_fields = ('title', 'author__name', 'isbn')
	list_filter = ('category', 'author')


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
	list_display = ('user', 'book', 'borrow_date', 'due_date', 'is_returned')
	list_filter = ('is_returned',)
	search_fields = ('user__username', 'book__title')
