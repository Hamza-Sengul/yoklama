from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import StudentProfile

def student_register(request):
    if request.method == 'POST':
        # Formdan gelen veriler
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        accept_privacy = request.POST.get('accept_privacy', None)
        student_number = request.POST.get('student_number', '').strip()
        student_class = request.POST.get('student_class', '').strip()  # '1', '2', '3' veya '4'
        department = request.POST.get('department', '').strip()

        # Tüm alanların doldurulup doldurulmadığını kontrol et
        if not all([first_name, last_name, email, password, confirm_password, student_number, student_class, department]):
            messages.error(request, "Tüm alanları doldurmalısınız.")
            return render(request, 'accounts/student_register.html', locals())

        # Email doğrulaması: @tarsus.edu.tr ile bitmeli
        if not email.endswith('@tarsus.edu.tr'):
            messages.error(request, "Email adresi @tarsus.edu.tr ile bitmelidir.")
            return render(request, 'accounts/student_register.html', locals())

        # Şifre kontrolü
        if password != confirm_password:
            messages.error(request, "Şifreler eşleşmiyor.")
            return render(request, 'accounts/student_register.html', locals())

        # Gizlilik sözleşmesi onayı kontrolü
        if accept_privacy != 'on':
            messages.error(request, "Gizlilik sözleşmesini kabul etmelisiniz.")
            return render(request, 'accounts/student_register.html', locals())

        # Sınıf seçimi kontrolü
        if student_class not in ['1', '2', '3', '4']:
            messages.error(request, "Sınıf seçimi geçersiz.")
            return render(request, 'accounts/student_register.html', locals())

        # Bölüm kontrolü (şu an için sadece 'Yönetim Bilişim Sistemleri')
        if department != "Yönetim Bilişim Sistemleri":
            messages.error(request, "Seçilebilecek bölüm: Yönetim Bilişim Sistemleri.")
            return render(request, 'accounts/student_register.html', locals())

        # Aynı email ile kayıtlı kullanıcı kontrolü
        if User.objects.filter(email=email).exists():
            messages.error(request, "Bu email ile kayıtlı bir kullanıcı zaten var.")
            return render(request, 'accounts/student_register.html', locals())

        # Kullanıcı oluşturma (username olarak email kullanılıyor)
        username = email
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Öğrenci profilini oluşturma
        StudentProfile.objects.create(
            user=user,
            student_number=student_number,
            student_class=int(student_class),
            department=department
        )

        login(request, user)
        messages.success(request, "Kayıt başarılı, sisteme giriş yapıldı.")
        return redirect('student_panel')

    return render(request, 'accounts/student_register.html')


def academic_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_superuser:
                login(request, user)
                return redirect('academic_panel')
            else:
                messages.error(request, "Bu giriş akademisyenlere özeldir.")
        else:
            messages.error(request, "Kullanıcı adı veya şifre hatalı.")
    return render(request, 'accounts/academic_login.html')


def student_login(request):
    next_url = request.GET.get('next')  # URL'den next parametresini alıyoruz
    if request.method == 'POST':
        username = request.POST.get('username')  # Email kullanılıyor
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not user.is_superuser:
                login(request, user)
                # Şifre değiştirme kontrolü:
                if user.studentprofile.must_change_password:
                    messages.info(request, "Lütfen ilk girişte şifrenizi değiştiriniz.")
                    # next parametresini de session'da saklayabiliriz, ancak burada basitçe password_change sayfasına yönlendiriyoruz.
                    return redirect('password_change')
                # Eğer next parametresi varsa onu kullanıyoruz
                if next_url:
                    return redirect(next_url)
                return redirect('student_panel')
            else:
                messages.error(request, "Bu giriş öğrenciler içindir.")
        else:
            messages.error(request, "Kullanıcı adı veya şifre hatalı.")
    return render(request, 'accounts/student_login.html', {'next': next_url})


from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Şifre değiştirildikten sonra must_change_password bayrağını False yapıyoruz.
        self.request.user.studentprofile.must_change_password = False
        self.request.user.studentprofile.save()
        return response

def student_panel(request):
    # Giriş yapmış öğrenciye ait yoklama kayıtlarını çekiyoruz.
    records = AttendanceRecord.objects.filter(student=request.user).order_by('-qr_session__created_at')
    return render(request, 'accounts/student_panel.html', {
        'records': records,
    })



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import StudentProfile, Course, Enrollment

# Önceki öğrenci ve akademisyen giriş/girişim view'leriniz burada yer alıyor...
# (student_register, student_login, academic_login, student_panel vs.)

def academic_panel(request):
    courses = Course.objects.all().order_by('-created_at')
    return render(request, 'accounts/academic_panel.html', {'courses': courses})






def course_update(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        course_code = request.POST.get('course_code', '').strip()
        course_name = request.POST.get('course_name', '').strip()

        if not course_code or not course_name:
            messages.error(request, "Lütfen ders kodu ve ders adını giriniz.")
            return redirect('course_update', course_id=course.id)

        # Güncelleme yaparken, mevcut dersin dışında aynı ders kodu varsa hata verelim.
        if Course.objects.filter(course_code__iexact=course_code).exclude(id=course.id).exists():
            messages.error(request, "Bu ders kodu zaten mevcut.")
            return redirect('course_update', course_id=course.id)

        course.course_code = course_code  # save() metodunda küçük harfe dönüştürülecek.
        course.course_name = course_name
        course.save()

        messages.success(request, "Ders başarıyla güncellendi.")
        return redirect('academic_panel')
    else:
        return render(request, 'accounts/course_update.html', {'course': course})

def course_create(request):
    if request.method == 'POST':
        course_code = request.POST.get('course_code', '').strip()
        course_name = request.POST.get('course_name', '').strip()

        if not course_code or not course_name:
            messages.error(request, "Lütfen ders kodu ve ders adını giriniz.")
            return render(request, 'accounts/course_create.html')

        # Ders kodu kontrolü (küçük-büyük harf duyarsız)
        if Course.objects.filter(course_code__iexact=course_code).exists():
            messages.error(request, "Bu ders kodu zaten mevcut.")
            return render(request, 'accounts/course_create.html')

        Course.objects.create(
            course_code=course_code,
            course_name=course_name,
            created_by=request.user
        )
        messages.success(request, "Ders başarıyla eklendi.")
        return redirect('academic_panel')
    else:
        return render(request, 'accounts/course_create.html')
    
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        course_code = request.POST.get('course_code', '').strip()
        course_name = request.POST.get('course_name', '').strip()
        if not course_code or not course_name:
            messages.error(request, "Lütfen ders kodu ve ders adını giriniz.")
            return redirect('course_detail', course_id=course.id)
        if Course.objects.filter(course_code__iexact=course_code).exclude(id=course.id).exists():
            messages.error(request, "Bu ders kodu zaten mevcut.")
            return redirect('course_detail', course_id=course.id)
        course.course_code = course_code
        course.course_name = course_name
        course.save()
        messages.success(request, "Ders başarıyla güncellendi.")
        return redirect('course_detail', course_id=course.id)
    enrollments = course.enrollments.all()
    return render(request, 'accounts/course_detail.html', {'course': course, 'enrollments': enrollments})

def course_enroll(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        # Seçilen öğrenciler checkbox ile gönderiliyor (birden fazla seçilebilecek)
        student_ids = request.POST.getlist('student_ids')
        if not student_ids:
            messages.error(request, "Lütfen en az bir öğrenci seçiniz.")
            return redirect('course_enroll', course_id=course.id)
        for student_id in student_ids:
            try:
                student = User.objects.get(id=student_id, is_superuser=False)
                if not course.enrollments.filter(student=student).exists():
                    Enrollment.objects.create(course=course, student=student)
            except User.DoesNotExist:
                continue
        messages.success(request, "Seçilen öğrenciler başarıyla derse eklendi.")
        return redirect('course_detail', course_id=course.id)
    else:
        # Halihazırda derse kayıtlı öğrencileri dışarıda bırakıyoruz
        enrolled_student_ids = course.enrollments.values_list('student_id', flat=True)
        # Sistemden, superuser olmayan öğrencilerin profillerini alıyoruz
        students = StudentProfile.objects.filter(user__is_superuser=False)\
                    .exclude(user__id__in=enrolled_student_ids)\
                    .order_by('student_class')
        # Öğrencileri sınıf bazında gruplandırıyoruz
        grouped_students = {}
        for student in students:
            group = student.student_class
            if group not in grouped_students:
                grouped_students[group] = []
            grouped_students[group].append(student)
        return render(request, 'accounts/course_enroll.html', {
            'course': course,
            'grouped_students': grouped_students
        })
    


import io, base64, qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Course, Enrollment, QrSession, AttendanceRecord, StudentProfile

# --- Önceki view'ler (öğrenci, akademisyen girişleri, ders ekleme, detay vs.) burada mevcut ---

# Sabitler (örnek amaçlı; gerçek uygulamada tarihsel hesaplamalar kullanılabilir)
CURRENT_WEEK = 3  
TOTAL_WEEKS = 14  

# 1. QR Oturumu Oluşturma (Form sayfası)
def qr_session_create(request):
    # Akademisyenin oluşturduğu dersleri getiriyoruz
    courses = Course.objects.filter(created_by=request.user)
    # Ayrıca derslere ait haftaları listelemek için range oluşturuyoruz.
    week_range = range(1, TOTAL_WEEKS+1)
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        week_number = request.POST.get('week_number')
        if not course_id or not week_number:
            messages.error(request, "Lütfen tüm alanları doldurunuz.")
            return render(request, 'accounts/qr_session_create.html', {
                'courses': courses,
                'current_week': CURRENT_WEEK,
                'total_weeks': TOTAL_WEEKS,
                'week_range': week_range
            })
        try:
            week_number = int(week_number)
        except ValueError:
            messages.error(request, "Geçersiz hafta numarası.")
            return render(request, 'accounts/qr_session_create.html', {
                'courses': courses,
                'current_week': CURRENT_WEEK,
                'total_weeks': TOTAL_WEEKS,
                'week_range': week_range
            })
        if week_number < CURRENT_WEEK:
            messages.error(request, "Geçmiş haftalar seçilemez.")
            return render(request, 'accounts/qr_session_create.html', {
                'courses': courses,
                'current_week': CURRENT_WEEK,
                'total_weeks': TOTAL_WEEKS,
                'week_range': week_range
            })
        course = get_object_or_404(Course, id=course_id)
        qr_session = QrSession.objects.create(
            course=course,
            week_number=week_number,
            created_by=request.user
        )
        # Dersin kayıtlı tüm öğrencileri için yoklama kaydı oluştur (varsayılan olarak "yok")
        for enrollment in course.enrollments.all():
            AttendanceRecord.objects.get_or_create(qr_session=qr_session, student=enrollment.student)
        messages.success(request, "QR Oturumu oluşturuldu.")
        return redirect('qr_session_display', session_id=qr_session.id)
    else:
        return render(request, 'accounts/qr_session_create.html', {
            'courses': courses,
            'current_week': CURRENT_WEEK,
            'total_weeks': TOTAL_WEEKS,
            'week_range': week_range
        })

def qr_session_display(request, session_id):
    qr_session = get_object_or_404(QrSession, id=session_id)
    # Sabit alan adını kullanarak tam URL oluşturuyoruz:
    attendance_url = f"https://tarsusuniversitesiqryoklama.online/qr_attendance/{session_id}/"
    
    # QR kod oluşturma işlemi:
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(attendance_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return render(request, 'accounts/qr_session_display.html', {
        'qr_session': qr_session,
        'qr_code': img_str
    })
# 3. QR Oturumunu Sonlandırma (Yoklamayı bitirme)
def qr_session_end(request, session_id):
    qr_session = get_object_or_404(QrSession, id=session_id)
    qr_session.is_active = False
    qr_session.ended_at = timezone.now()
    qr_session.save()
    messages.success(request, "QR Oturumu sonlandırıldı.")
    return redirect('academic_panel')  # veya yoklama kayıtları sayfasına yönlendirin

# 4. Öğrenci, QR Kod taraması ile yoklamayı alır
@login_required
def qr_attendance(request, session_id):
    qr_session = get_object_or_404(QrSession, id=session_id, is_active=True)
    try:
        record = AttendanceRecord.objects.get(qr_session=qr_session, student=request.user)
    except AttendanceRecord.DoesNotExist:
        messages.error(request, "Bu derse kayıtlı değilsiniz.")
        return redirect('student_panel')
    record.present = True
    record.save()
    messages.success(request, "Yoklamanız alındı.")
    return redirect('student_panel')

# 5. Akademisyenin yoklama kayıtlarını görüntüleyebileceği sayfa
def attendance_record_list(request):
    qr_sessions = QrSession.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'accounts/attendance_record_list.html', {'qr_sessions': qr_sessions})

