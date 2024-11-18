import os

from django.shortcuts import render
from redis import Redis

# Create your views here.
from .ScrapingTask import scrape_linkedin
import json
from django.db.models import Prefetch
from django.shortcuts import render
from django.db.models import Count
import configparser
from django.db.models import Count, Sum, F, ExpressionWrapper
from decimal import Decimal
import datetime
import xml.etree.ElementTree as ET
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .Forms import CustomUserCreationForm
from django.contrib.auth import logout
from django.contrib.auth import login
from .Forms import LoginForm
from django.contrib.auth.decorators import login_required
import openpyxl
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest

from .models import Person, Company


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'PartnershipsFinder/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('/index')
            else:
                form.add_error(None, 'Invalid email or password.')
    else:
        form = LoginForm()
    return render(request, 'PartnershipsFinder/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('/login')


def getdata():
    match_url = "https://media.licdn.com/dms/image/v2/D4D03AQHoHh3c5w12xA/"
    replacement_url = "https://i.imgur.com/mUtO8vh.jpg"
    all_persons_data = Person.objects.all().values('url', 'name', 'title', 'location', 'company__name',
                                                   'img_url')
    processed_data = []
    for person in all_persons_data:
        if person['img_url'].startswith(match_url):
            person['img_url'] = replacement_url
        processed_data.append(person)

    return processed_data


@login_required
def results(request):
    order = request.GET.get('order', 'asc')
    search_query = request.GET.get('q', '')
    data = getdata()

    if search_query:
        data = [d for d in data if search_query.lower() in d['name'].lower()]

    if order == 'asc':
        data = sorted(data, key=lambda x: x['name'])
    elif order == 'desc':
        data = sorted(data, key=lambda x: x['name'], reverse=True)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'data': data})

    return render(request, 'PartnershipsFinder/scrapedData.html', {'data': data, 'order': order})


@login_required
def resultsbycompany(request):
    order = request.GET.get('order', 'asc')
    search_query = request.GET.get('q', '')

    companies = Company.objects.prefetch_related(
        Prefetch('person_set', queryset=Person.objects.all())
    )

    if search_query:
        companies = companies.filter(name__icontains=search_query)

    if order == 'asc':
        companies = companies.order_by('name')
    elif order == 'desc':
        companies = companies.order_by('-name')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        company_data = [
            {
                'name': company.name,
                'persons': [{'name': person.name, 'email': person.email} for person in company.person_set.all()]
            }
            for company in companies
        ]
        return JsonResponse({'companies': company_data})

    return render(request, 'PartnershipsFinder/ScrapedDatacOMPANIES.html', {'companies': companies, 'order': order})


def get_company_members(request):
    company_id = request.GET.get('company_id')
    if company_id:
        members = Person.objects.filter(company_id=company_id).values('name', 'url', 'email', 'title', 'location')
        return JsonResponse({'members': list(members)})
    return JsonResponse({'members': []})


@login_required
def delete_company(request):
    if request.method == 'POST':
        company_id = request.POST.get('company_id')
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
                company.delete()
                return JsonResponse({'success': True})
            except Company.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Company not found.'})
        return JsonResponse({'success': False, 'message': 'Invalid company ID.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required
def delete_session(request):
    label_to_delete = request.POST.get('label')

    tree = ET.parse('scraping_history.xml')
    root = tree.getroot()

    for job in root.findall('job'):
        label = job.find('label').text
        if label == label_to_delete:
            root.remove(job)
            tree.write('scraping_history.xml')
            break

    return redirect(reverse('history'))


@login_required
def history(request):
    tree = ET.parse('scraping_history.xml')
    root = tree.getroot()

    jobs = []
    for job in root.findall('job'):
        label = job.find('label').text
        ct_num = job.find('ct_num').text
        title = job.find('title').text
        industry = job.find('industry').text
        start_time = job.find('start_time').text
        end_time = job.find('end_time').text
        jobs.append({
            'label': label,
            'title': title,
            'industry': industry,
            'ct_num': ct_num,
            'start_time': start_time,
            'end_time': end_time,
        })
    return render(request, 'PartnershipsFinder/JobHistory.html', {'sessions': jobs})


@login_required
def index(request):
    today = datetime.now()
    formatted_date = today.strftime("%a, %d %b %Y")
    config = configparser.ConfigParser()
    config.read('web.config')
    average_salary = Decimal(config.get('Settings', 'average_salary', fallback='0'))
    currency = config.get('Settings', 'currency', fallback='USD')

    excluded_employees = Person.objects.filter(
        company__name__in=['ESPRIT', 'Ecole Supérieure Privée d\'Ingénierie et de Technologies - ESPRIT']
    ).count()

    total_employees = Person.objects.count()
    included_employees = total_employees - excluded_employees

    total_salary = included_employees * average_salary

    if total_salary >= Decimal(1_000_000):
        total_salary_display = f"{total_salary / Decimal(1_000_000):.1f}M"
    else:
        total_salary_display = f"{total_salary:,.0f}".replace(",", " ")

    company_employee_counts = Company.objects.annotate(employee_count=Count('person')).exclude(
        name__in=['ESPRIT', 'Ecole Supérieure Privée d\'Ingénierie et de Technologies - ESPRIT']
    )

    chart_data = {
        'labels': [company.name for company in company_employee_counts],
        'data': [company.employee_count for company in company_employee_counts],
    }

    return render(request, 'PartnershipsFinder/index.html', {
        'num_students': total_employees,
        'num_companies': Company.objects.count(),
        'excluded_employees': excluded_employees,
        'chart_data': json.dumps(chart_data),
        'total_salary': total_salary_display,
        'currency': currency,
        'date': formatted_date,
    })


@login_required
def start_scraping(request):
    if request.method == 'POST':
        try:
            ct_num = int(request.POST.get('ct_num'))
            title = str(request.POST.get('title'))
            label = request.POST.get('label')

            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            redis_conn = Redis(host='192.168.0.18', port=6379, db=1)
            redis_conn.set('scraping_progress', json.dumps({'progress': 0, 'step': 0, 'total_steps': ct_num}))
            redis_conn.set('scraped_data', json.dumps([]))

            xml_file = 'scraping_history.xml'
            if not os.path.exists(xml_file):
                root = ET.Element("scraping_history")
            else:
                tree = ET.parse(xml_file)
                root = tree.getroot()

            job = ET.SubElement(root, "job")
            ET.SubElement(job, "label").text = label
            ET.SubElement(job, "ct_num").text = str(ct_num)
            ET.SubElement(job, "title").text = str(title)
            ET.SubElement(job, "start_time").text = start_time
            ET.SubElement(job, "end_time").text = ""

            tree = ET.ElementTree(root)
            tree.write(xml_file)

            scrape_linkedin.delay(ct_num, title)
            return render(request, 'PartnershipsFinder/progress.html')

        except ValueError:
            return HttpResponseBadRequest("Invalid input. Please provide valid numbers.")
    else:
        return redirect('results')


@login_required
def resultsbycompany(request):
    order = request.GET.get('order', 'asc')
    search_query = request.GET.get('q', '')

    companies = Company.objects.prefetch_related(
        Prefetch('person_set', queryset=Person.objects.all())
    )

    if search_query:
        companies = companies.filter(name__icontains=search_query)

    if order == 'asc':
        companies = companies.order_by('name')
    elif order == 'desc':
        companies = companies.order_by('-name')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        company_data = [
            {
                'name': company.name,
                'persons': [{'name': person.name, 'email': person.email} for person in company.person_set.all()]
            }
            for company in companies
        ]
        return JsonResponse({'companies': company_data})

    return render(request, 'PartnershipsFinder/ScrapedDatacOMPANIES.html', {'companies': companies, 'order': order})


@login_required
def export(request):

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Contacts"

    headers = ['URL', 'Name', 'Email', 'Title', 'Location', 'Company']
    ws.append(headers)

    contacts = Person.objects.all()

    for contact in contacts:
        ws.append([
            contact.url,
            contact.name,
            contact.email,
            contact.title,
            contact.location,
            contact.company.name if contact.company else 'N/A'
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=contacts.xlsx'
    wb.save(response)

    return response


@login_required
def delete_session(request):
    label_to_delete = request.POST.get('label')

    tree = ET.parse('scraping_history.xml')
    root = tree.getroot()

    for job in root.findall('job'):
        label = job.find('label').text
        if label == label_to_delete:
            root.remove(job)
            tree.write('scraping_history.xml')
            break

    return redirect(reverse('history'))
# Create your views here.
