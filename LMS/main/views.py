from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django import forms
from .models import Book, Author, Category, BorrowRecord

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def book_list(request):
    query = request.GET.get('q', '')
    if query:
        books = Book.objects.filter(
            Q(title__icontains=query) |
            Q(author__name__icontains=query) |
            Q(category__name__icontains=query)
        )
    else:
        books = Book.objects.all()
    return render(request, 'book_list.html', {'books': books, 'query': query})

@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    # Refresh from database to ensure latest copies_available
    book.refresh_from_db()
    can_borrow = book.copies_available > 0
    return render(request, 'book_detail.html', {'book': book, 'can_borrow': can_borrow})

@login_required
def borrow_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.refresh_from_db()  # Ensure we have the latest data

    # Prevent duplicate pending/approved borrow records for the same book/user
    existing_borrow = BorrowRecord.objects.filter(
        user=request.user,
        book=book,
        is_returned=False
    ).exists()

    if existing_borrow:
        can_borrow = book.copies_available > 0
        return render(request, 'book_detail.html', {
            'book': book,
            'can_borrow': can_borrow,
            'alert_message': f'You have already requested or borrowed this book. Please return it before borrowing again.'
        })

    # Create a borrow request (pending approval)
    if book.copies_available > 0:
        BorrowRecord.objects.create(user=request.user, book=book, is_approved=False)
        messages.success(request, f'Borrow request submitted for "{book.title}". An admin will approve it soon.')
    else:
        messages.error(request, f'Sorry, no copies of "{book.title}" are currently available')
    return redirect('book_detail', pk=pk)

@login_required
def return_book(request, pk):
    borrow_record = get_object_or_404(BorrowRecord, pk=pk, user=request.user, is_returned=False)
    borrow_record.is_returned = True
    borrow_record.return_date = timezone.now()
    borrow_record.save()
    messages.success(request, f'You have returned "{borrow_record.book.title}"')
    return redirect('profile')

@login_required
def profile(request):
    borrowed_books = BorrowRecord.objects.filter(user=request.user, is_returned=False)
    return render(request, 'profile.html', {'borrowed_books': borrowed_books})

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('home')
    books = Book.objects.all()
    authors = Author.objects.all()
    categories = Category.objects.all()
    borrow_records = BorrowRecord.objects.all()
    return render(request, 'admin_dashboard.html', {
        'books': books,
        'authors': authors,
        'categories': categories,
        'borrow_records': borrow_records
    })

# Author CRUD
@login_required
def author_list(request):
    if not request.user.is_staff:
        return redirect('home')
    authors = Author.objects.all()
    return render(request, 'author_list.html', {'authors': authors})

@login_required
def author_create(request):
    if not request.user.is_staff:
        return redirect('home')
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Author created successfully.')
            return redirect('author_list')
    else:
        form = AuthorForm()
    return render(request, 'author_form.html', {'form': form, 'title': 'Create Author'})

@login_required
def author_update(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    author = get_object_or_404(Author, pk=pk)
    if request.method == 'POST':
        form = AuthorForm(request.POST, instance=author)
        if form.is_valid():
            form.save()
            messages.success(request, 'Author updated successfully.')
            return redirect('author_list')
    else:
        form = AuthorForm(instance=author)
    return render(request, 'author_form.html', {'form': form, 'title': 'Update Author'})

@login_required
def author_delete(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    author = get_object_or_404(Author, pk=pk)
    if request.method == 'POST':
        author.delete()
        messages.success(request, 'Author deleted successfully.')
        return redirect('author_list')
    return render(request, 'author_confirm_delete.html', {'author': author})

# Category CRUD
@login_required
def category_list(request):
    if not request.user.is_staff:
        return redirect('home')
    categories = Category.objects.all()
    return render(request, 'category_list.html', {'categories': categories})

@login_required
def category_create(request):
    if not request.user.is_staff:
        return redirect('home')
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully.')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'category_form.html', {'form': form, 'title': 'Create Category'})

@login_required
def category_update(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'category_form.html', {'form': form, 'title': 'Update Category'})

@login_required
def category_delete(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully.')
        return redirect('category_list')
    return render(request, 'category_confirm_delete.html', {'category': category})

# Book CRUD
@login_required
def book_admin_list(request):
    if not request.user.is_staff:
        return redirect('home')
    books = Book.objects.all()
    return render(request, 'book_admin_list.html', {'books': books})

@login_required
def book_create(request):
    if not request.user.is_staff:
        return redirect('home')
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book created successfully.')
            return redirect('book_admin_list')
    else:
        form = BookForm()
    return render(request, 'book_form.html', {'form': form, 'title': 'Create Book'})

@login_required
def book_update(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book updated successfully.')
            return redirect('book_admin_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'book_form.html', {'form': form, 'title': 'Update Book'})

@login_required
def book_delete(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Book deleted successfully.')
        return redirect('book_admin_list')
    return render(request, 'book_confirm_delete.html', {'book': book})

# BorrowRecord CRUD
@login_required
def borrow_record_create(request):
    if not request.user.is_staff:
        return redirect('home')
    if request.method == 'POST':
        form = BorrowRecordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Borrow record created successfully.')
            return redirect('borrow_record_list')
    else:
        form = BorrowRecordForm()
    return render(request, 'borrow_record_form.html', {'form': form, 'title': 'Create Borrow Record'})

@login_required
def borrow_record_list(request):
    if not request.user.is_staff:
        return redirect('home')

    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', 'all')

    borrow_records = BorrowRecord.objects.all()

    if query:
        borrow_records = borrow_records.filter(user__username__icontains=query)

    if status == 'returned':
        borrow_records = borrow_records.filter(is_returned=True)
    elif status == 'not_returned':
        borrow_records = borrow_records.filter(is_returned=False)

    return render(request, 'borrow_record_list.html', {
        'object_list': borrow_records,
        'query': query,
        'status': status,
    })

@login_required
def incoming_borrow_requests(request):
    if not request.user.is_staff:
        return redirect('home')

    requests = BorrowRecord.objects.filter(is_approved=False, is_returned=False)
    return render(request, 'incoming_borrow_requests.html', {'requests': requests})

@login_required
def approve_borrow_request(request, pk):
    if not request.user.is_staff:
        return redirect('home')

    borrow_record = get_object_or_404(BorrowRecord, pk=pk, is_approved=False, is_returned=False)
    book = borrow_record.book

    if book.copies_available <= 0:
        messages.error(request, f"Cannot approve request: '{book.title}' has no available copies.")
        return redirect('incoming_borrow_requests')

    borrow_record.is_approved = True
    borrow_record.save()

    messages.success(request, f"Borrow request for '{book.title}' has been approved.")
    return redirect('incoming_borrow_requests')

@login_required
def reject_borrow_request(request, pk):
    if not request.user.is_staff:
        return redirect('home')

    borrow_record = get_object_or_404(BorrowRecord, pk=pk, is_approved=False, is_returned=False)
    borrow_record.delete()
    messages.success(request, f"Borrow request for '{borrow_record.book.title}' has been rejected.")
    return redirect('incoming_borrow_requests')

@login_required
def borrow_record_update(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    borrow_record = get_object_or_404(BorrowRecord, pk=pk)
    if request.method == 'POST':
        form = BorrowRecordForm(request.POST, instance=borrow_record)
        if form.is_valid():
            form.save()
            messages.success(request, 'Borrow record updated successfully.')
            return redirect('borrow_record_list')
    else:
        form = BorrowRecordForm(instance=borrow_record)
    return render(request, 'borrow_record_form.html', {'form': form, 'title': 'Update Borrow Record'})

@login_required
def borrow_record_delete(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    borrow_record = get_object_or_404(BorrowRecord, pk=pk)
    if request.method == 'POST':
        borrow_record.delete()
        messages.success(request, 'Borrow record deleted successfully.')
        return redirect('borrow_record_list')
    return render(request, 'borrow_record_confirm_delete.html', {'borrow_record': borrow_record})

# Forms
class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['name', 'bio']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'category', 'isbn', 'published_date', 'copies_available', 'description', 'image']

class BorrowRecordForm(forms.ModelForm):
    class Meta:
        model = BorrowRecord
        fields = ['user', 'book', 'borrow_date', 'due_date', 'return_date', 'is_returned']
