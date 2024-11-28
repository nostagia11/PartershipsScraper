from django.contrib import messages

# Create your views here.
from django.db.models import Prefetch
from django.shortcuts import render
from django.db.models import Count
import datetime
import xml.etree.ElementTree as ET
from django.shortcuts import redirect
from datetime import datetime
from django.http import HttpResponseBadRequest
from django.contrib.auth import authenticate
from .Forms import CustomUserCreationForm
from django.contrib.auth import login
from .Forms import LoginForm
from django.contrib.auth.decorators import login_required
import openpyxl
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest

from .Uniscrape import scrape_uni
from .models import Person, Company


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'PartnershipsFinder/authentication/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('/index')
            else:
                messages.error(request, "Invalid username or password.")  # Use Django's messaging framework
        else:
            messages.error(request, "Form validation failed.")
    else:
        form = LoginForm()
    return render(request, 'PartnershipsFinder/authentication/login.html', {'form': form})


@login_required(login_url="/login")
def getdata(request):
    all_persons_data = Person.objects.all().values('url', 'name', 'title', 'location', 'company__name'
                                                   )
    contacts = []
    for contact in all_persons_data:
        contacts.append(contact)

    return contacts


@login_required(login_url="/login")
def results(request):
    order = request.GET.get('order', 'asc')
    search_query = request.GET.get('q', '')
    data = getdata(request)

    if search_query:
        data = [d for d in data if search_query.lower() in d['name'].lower()]

    if order == 'asc':
        data = sorted(data, key=lambda x: x['name'])
    elif order == 'desc':
        data = sorted(data, key=lambda x: x['name'], reverse=True)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'data': data})

    return render(request, 'PartnershipsFinder/scrapedData.html', {'data': data, 'order': order})


@login_required(login_url="/login")
def resultsbycompany(request):
    # match_url = "https://media.licdn.com/dms/image/v2/D4D03AQHoHh3c5w12xA/"
    # replacement_url = "https://i.imgur.com/mUtO8vh.jpg"
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


@login_required(login_url="/login")
def get_company_members(request):
    company_id = request.GET.get('company_id')
    if company_id:
        members = Person.objects.filter(company_id=company_id).values('name', 'url', 'email', 'title', 'location')
        return JsonResponse({'members': list(members)})
    return JsonResponse({'members': []})


@login_required(login_url="/login")
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


@login_required(login_url="/login")
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
    return render(request, 'PartnershipsFinder/JobHistory.html', {'jobs': jobs})


@login_required(login_url="/login")
def index(request):
    # today = datetime.now()
    # formatted_date = today.strftime("%a, %d %b %Y")
    # config = configparser.ConfigParser()
    # config.read('web.config')
    # average_salary = Decimal(config.get('Settings', 'average_salary', fallback='0'))
    # currency = config.get('Settings', 'currency', fallback='USD')

    """total_salary = companies_contacts * average_salary

    if total_salary >= Decimal(1_000_000):
        total_salary_display = f"{total_salary / Decimal(1_000_000):.1f}M"
    else:
        total_salary_display = f"{total_salary:,.0f}".replace(",", " ")"""

    """uni_contacts_counts = Company.objects.annotate(employee_count=Count('person')).exclude(
        industry__in=['IT Services and IT Consulting', 'Software Development']
    )"""
    """total_contacts = Person.objects.count()
    industry_contacts_counts = total_contacts - uni_contacts_counts"""

    uni_companies = Company.objects.filter(
        industry__in=['Higher Education']
    ).count()

    total_companies = Company.objects.count()
    industry_companies = total_companies - uni_companies

    return render(request, 'PartnershipsFinder/index.html', {

        'uni_companies': uni_companies,
        'industry_companies': industry_companies

    })


def stats():
    # Group by industry and count the related Person objects (contacts)
    chart_data = Company.objects.annotate(contact_count=Count('person')).values('industry', 'contact_count')

    # Extract data into lists for the chart
    industries = [entry['industry'] for entry in chart_data]
    contact_counts = [entry['contact_count'] for entry in chart_data]

    return JsonResponse({'data': chart_data}, safe=False)


"""return render(request, 'PartnershipsFinder/index.html', {
    'num_students': total_contacts,
    'num_companies': Company.objects.count(),
    'companies_contacts': companies_contacts,
    'chart_data': json.dumps(chart_data),
    'total_salary': total_salary_display,
    'currency': currency,
    'date': formatted_date,
})"""


@login_required(login_url="/login")
def start_scraping(request):
    if request.method == 'POST':
        try:
            #ct_num = int(request.POST.get('ct_num'))
            industry = str(request.POST.get('industry'))
            label = request.POST.get('label')

            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            #redis_conn = Redis(host='192.168.0.18', port=6379, db=1)
            #redis_conn.set('scraping_progress', json.dumps({'progress': 0, 'step': 0, 'total_steps': ct_num}))
            #redis_conn.set('scraped_data', json.dumps([]))

            #xml_file = 'scraping_history.xml'
            """if not os.path.exists(xml_file):
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
            tree.write(xml_file)"""

            scrape_uni()
            return render(request, 'PartnershipsFinder/scrapedData.html')

        except ValueError:
            return HttpResponseBadRequest("Invalid input. Please provide valid numbers.")
    else:
        return redirect('results')


@login_required(login_url="/login")
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

        # Sheet 2: Exporting "Company" data
    ws_companies = wb.create_sheet(title="Companies")
    headers_companies = ['Name', 'Industry', 'Phone', 'Location', 'Image URL', 'Website URL', 'URL']
    ws_companies.append(headers_companies)

    companies = Company.objects.all()
    for company in companies:
        ws_companies.append([
            company.name,
            company.industry,
            company.phone,
            company.location,
            company.img_url,
            company.website_url,
            company.url,
            # company.company.name if company.company else 'N/A'
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=ScrapedCompaniesContacts.xlsx'
    wb.save(response)

    return response


@login_required(login_url="/login")
def delete_session(request):
    label_to_delete = request.POST.get('label')

    # Validate input
    if not label_to_delete:
        return HttpResponseBadRequest("Invalid label provided.")

    try:
        # Parse the XML file
        tree = ET.parse('scraping_history.xml')
        root = tree.getroot()

        # Find and remove the matching job
        job_found = False
        for job in root.findall('job'):
            label = job.find('label').text
            if label == label_to_delete:
                root.remove(job)
                job_found = True
                break

        if not job_found:
            return HttpResponseBadRequest("Label not found.")

        # Write back to the file
        tree.write('scraping_history.xml')
    except FileNotFoundError:
        return HttpResponseBadRequest("XML file not found.")
    except ET.ParseError:
        return HttpResponseBadRequest("Error parsing XML file.")
    except Exception as e:
        return HttpResponseBadRequest(f"An unexpected error occurred: {e}")

    # Redirect to history page
    return redirect('history')
# Create your views here.





