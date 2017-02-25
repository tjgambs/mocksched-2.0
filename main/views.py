from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext
from django.template import Context, Template
from django.template.loader import get_template
import urllib, json, requests, xmltodict, math


def index(request):
	template = get_template('main.html')
	context = Context({
		'terms':getTerms(),
		'subjects':getSubjects(),
	})
	return HttpResponse(template.render(context))


def search(request,stream,subject,catalog_nbr=''):
	template = get_template('search.html')
	classes = getClasses(stream,subject,catalog_nbr)

	context = Context({
		'currentStream':stream,
		'response':classes[0],
		'subjects':getSubjects(),
		'terms':getTerms(),
		'currentSubject':subject,
		'currentClassNumber':catalog_nbr,
		'numberOfClasses':classes[1],
	})
	return HttpResponse(template.render(context))


def cart(request):
	template = get_template('cart.html')
	context = Context({
			'subjects':getSubjects(),
			'terms':getTerms()
		})
	return HttpResponse(template.render(context))


def add_to_cart(request):
	if request.method == 'POST':
		data = dict(request.POST)
		if request.session.get('courseCart') == None or request.session.get('courseCart') == []:
			request.session['courseCart'] = [data]
		else:
			request.session['courseCart'].append(data)

		print(request.session.get('courseCart'))
		return HttpResponse('Location endpoint.')
	else:
		return HttpResponse('Location endpoint.')


def getTerms():
	terms = urllib.urlopen('http://offices.depaul.edu/_layouts/DUC.SR.ClassSvc/DUClassSvc.ashx?action=getterms').read()
	json_terms = json.loads(terms.decode('utf-8'))
	return json_terms


def getSubjects():
	subjects = urllib.urlopen('http://offices.depaul.edu/_layouts/DUC.SR.ClassSvc/DUClassSvc.ashx?action=getsubjects').read()
	json_subjects = json.loads(subjects.decode('utf-8'))
	return json_subjects


def getClasses(stream,subject,catalog_nbr):
	classes = urllib.urlopen('http://offices.depaul.edu/_layouts/DUC.SR.ClassSvc/DUClassSvc.ashx?action=searchclassbysubject&strm={0}&subject={1}&catalog_nbr={2}'.format(stream,subject,catalog_nbr)).read()
	json_classes = json.loads(classes.decode('utf-8'))
	class_data = classData()
	num = 0
	for j in json_classes:
		for k in j['classes']:
			try:
				k['data'] = class_data.get(k['subject'] + ' ' + k['catalog_nbr'])['@ows_DESCR']
			except Exception as e:
				k['data'] = 'No course description preview available. Click to find out more about ' + k['subject'] + ' ' + k['catalog_nbr'] + "."
			num+=1
	return [json_classes,num]


def classData():
	# url = "http://www.depaul.edu/university-catalog/_vti_bin/Lists.asmx"
	# headers = {'content-type': 'text/xml'}
	# body =   """<soap:Envelope xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xsd='http://www.w3.org/2001/XMLSchema' xmlns:soap='http://schemas.xmlsoap.org/soap/envelope/'>
	# 				<soap:Body>
	# 					<GetListItems xmlns='http://schemas.microsoft.com/sharepoint/soap/'>
	# 					<listName>Courses</listName>
	# 					<viewName></viewName>
	# 					<query>
	# 						<Query></Query>
	# 					</query>
	# 					<viewFields>
	# 						<ViewFields>
	# 							<FieldRef Name='Title' />
	# 							<FieldRef Name='SUBJECT' />
	# 							<FieldRef Name='CATALOG_NBR' />
	# 							<FieldRef Name='ACAD_CAREER' />
	# 							<FieldRef Name='DESCR' />
	# 							<FieldRef Name='Prerequisites' />
	# 						</ViewFields>
	# 					</viewFields>
	# 					<rowLimit>0</rowLimit>
	# 					<queryOptions><QueryOptions>
	# 					</QueryOptions></queryOptions>
	# 					</GetListItems>
	# 				</soap:Body>
	# 			</soap:Envelope>"""

	# response = requests.post(url,data=body,headers=headers)
	# class_list = xmltodict.parse(response.content)['soap:Envelope']['soap:Body']['GetListItemsResponse']['GetListItemsResult']['listitems']['rs:data']['z:row']
	# dic = {}
	# for c in class_list:
	# 	try:
	# 		dic[c.get('@ows_SUBJECT') + ' ' + c.get('@ows_CATALOG_NBR')] = c
	# 	except Exception,e:
	# 		continue
	with open('courseDescriptions.json','r') as i:
		dic = json.loads(i.read())
	return dic


def page(request,stream,subject,num):
	ratings = getRatings()
	course = urllib.urlopen('http://offices.depaul.edu/_layouts/DUC.SR.ClassSvc/DUClassSvc.ashx?action=getcourse&strm={0}&subject={1}&catalog_nbr={2}'.format(stream,subject,num)).read()
	json_course = json.loads(course.decode('utf-8'))
	template = get_template('page.html')
	name = json_course.get('descr')
	description = json_course.get('descrlong')

	classes = urllib.urlopen('http://offices.depaul.edu/_layouts/DUC.SR.ClassSvc/DUClassSvc.ashx?action=getclasses&strm={0}&subject={1}&catalog_nbr={2}'.format(stream,subject,num)).read()
	json_classes = json.loads(classes.decode('utf-8'))
	headers0 = ['Add','Rating','Status','Credits','Instructor','Start','End','Section','Number','Location','Days']
	headers1 = ['Add','Rating','Status','Credits','Topic','Instructor','Start','End','Section','Number','Location','Days']
	arr = []
	pk_ids = []
	for j in json_classes:
		topic = j['topic_descr'].title()
		number = j.get('class_nbr')
		section = j.get('class_section')
		credits = j.get('units_acad_prog')
		status = j.get('enrl_stat')
		if status == 'O':
			status = '<font color="green">Open</font>'
		elif status == 'C':
			status = '<font color="red">Closed</font>'
		else:
			status = '<font color="yellow">Waitlist</font>'
		instructor = j.get('first_name') + ' ' + j.get('last_name')
		location = j.get('location_descr')
		start = j.get('meeting_time_start').replace('1/1/1900 ','').replace(':00 ',' ')
		end = j.get('meeting_time_end').replace('1/1/1900 ','').replace(':00 ',' ')
		days = formatDays(j)
		rating = ratings.get(j.get('first_name') + ' ' + j.get('last_name'))
		if rating == None:
			rating = 'N/A'
		else:
			href = '/ratings/'+str(rating[-1])+'/1/'+str(rating[0])+'/'+str(rating[1])+'/'+str(rating[2])+'/'+str(rating[3])+'/'+instructor+'/'+stream+'/'+subject+'/'+num+'/'
			rating = '<a style="text-decoration:none;" href="'+href+'">' + str(rating[0]) + '</a>'
			instructor = '<a style="text-decoration:none;" href="'+href+'">' + instructor + '</a>'
		if topic == '':
			headers = headers0
			arr.append([rating,status,credits,instructor,start,end,section,number,location,days])
		else:
			headers = headers1
			arr.append([rating,status,credits,topic,instructor,start,end,section,number,location,days])
		
		pk_ids.append(j.get('pk_id'))

	context = Context({
		'subjects':getSubjects(),
		'name':name,
		'description':description,
		'headers':headers,
		'classes':arr,
		'pk_ids':pk_ids,
		'stream':stream,
		'currentSubject':subject,
		'currentClassNumber':num
	})
	return HttpResponse(template.render(context))


def getRatings():
	law = urllib.urlopen('http://search.mtvnservices.com/typeahead/suggest/?solrformat=true&rows=10000000&q=*%253A*+AND+schoolid_s%253A5485&defType=edismax&qf=teacherfullname_t%255E1000+autosuggest&bf=pow(total_number_of_ratings_i%252C2.1)&sort=&siteName=rmp&rows=1000000000&start=0&fl=pk_id+teacherfirstname_t+teacherlastname_t+averageratingscore_rf+averagehelpfulscore_rf+averageclarityscore_rf+averageeasyscore_rf').read()
	json_law = json.loads(law.decode('utf-8'))
	regular = urllib.urlopen('http://search.mtvnservices.com/typeahead/suggest/?solrformat=true&rows=1000000&q=*%253A*+AND+schoolid_s%253A1389&defType=edismax&qf=teacherfullname_t%255E1000+autosuggest&bf=pow(total_number_of_ratings_i%252C2.1)&sort=&siteName=rmp&rows=1000000000&start=0&fl=pk_id+teacherfirstname_t+teacherlastname_t+averageratingscore_rf+averagehelpfulscore_rf+averageclarityscore_rf+averageeasyscore_rf').read()
	json_regular = json.loads(regular.decode('utf-8'))
	complete = json_law['response']['docs'] + json_regular['response']['docs']
	dic = {}
	for c in complete:
		first_name = c.get('teacherfirstname_t')
		last_name = c.get('teacherlastname_t')
		average_rating = c.get('averageratingscore_rf')
		average_helpful_rating = c.get('averagehelpfulscore_rf')
		average_clarity_rating = c.get('averageclarityscore_rf')
		average_easy_rating = c.get('averageeasyscore_rf')
		pk_id = c.get('pk_id')
		dic[first_name + ' ' + last_name] = [average_rating,average_helpful_rating,average_clarity_rating,average_easy_rating,pk_id]
	return dic


def formatDays(obj):
	arr = []
	for i in obj:
		if obj[i] == 'Y':
			if 'm' == i[0] or 'w' == i[0]:
				arr.append(i[0].upper())
			else:
				arr.append(i[0].upper()+i[1].lower())
	ret = ''.join(arr)
	if ret == 'ThTu':
		ret = 'TuTh'
	elif ret == 'WM':
		ret = 'MW'
	return ret


def teacher(request,tid,page,average_rating,average_helpful,average_clarity,average_easy,name,stream,subject,num):
	reviews = urllib.urlopen('http://www.ratemyprofessors.com/paginate/professors/ratings?tid={0}&page={1}'.format(tid,page)).read()
	json_data = json.loads(reviews.decode('utf-8'))
	json_reviews = json_data['ratings']
	reviews = []
	for j in json_reviews:
		dic = {}
		dic['date'] = j.get('rDate')
		dic['class'] = j.get('rClass')
		dic['helpful'] = j.get('rHelpful')
		dic['clarity'] = j.get('rClarity')
		dic['easy'] = j.get('rEasy')
		dic['grade'] = j.get('teacherGrade')
		dic['comments'] = j.get('rComments')
		reviews.append(dic)

	json_remaining = json_data['remaining']
	if page != 1:
		num_pages = math.ceil((len(json_reviews) + json_remaining + (int(page) * 20)) / 20) 
	else:
		num_pages = math.ceil((len(json_reviews) + json_remaining) / 20)

	pages = []
	for n in range(1,int(num_pages) + 1):
		href = '/ratings/{0}/{1}/{2}/{3}/{4}/{5}/{6}/{7}/{8}/{9}/'.format(tid,n,average_rating,average_helpful,average_clarity,average_easy,name,stream,subject,num)
		pages.append({'number':n,'href':href})

	template = get_template('teacher.html')

	context = Context({
		'instructor':name,
		'overall_quality':average_rating,
		'helpfulness':average_helpful,
		'clarity':average_clarity,
		'easiness':average_easy,
		'reviews':reviews,
		'subjects':getSubjects(),
		'currentSubject':subject,
		'currentClassNumber':num,
		'stream':stream,
		'pages':pages,
		'currentPage':int(page)
	})

	return HttpResponse(template.render(context))
