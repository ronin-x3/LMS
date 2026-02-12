from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
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
    
    if book.copies_available > 0:
        BorrowRecord.objects.create(user=request.user, book=book)
        book.copies_available -= 1
        book.save()
        messages.success(request, f'You have borrowed "{book.title}"')
    else:
        messages.error(request, f'Sorry, no copies of "{book.title}" are currently available')
    return redirect('book_detail', pk=pk)

@login_required
def return_book(request, pk):
    borrow_record = get_object_or_404(BorrowRecord, pk=pk, user=request.user, is_returned=False)
    borrow_record.is_returned = True
    borrow_record.return_date = timezone.now()
    borrow_record.save()
    borrow_record.book.copies_available += 1
    borrow_record.book.save()
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
