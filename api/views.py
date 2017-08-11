import requests
from bs4 import BeautifulSoup
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.core import serializers
from api.models import CourseCode, Course

BASE_URL = "http://www.sis.itu.edu.tr/tr/ders_programlari/LSprogramlar/prg.php?fb="


@user_passes_test(lambda u: u.is_superuser)
def refresh_course_codes(request):
    CourseCode.objects.all().delete()

    r = requests.get(BASE_URL)
    soup = BeautifulSoup(r.content, "html.parser")

    for option in soup.find("select").find_all("option"):
        if option.attrs["value"] != "":
            CourseCode.objects.create(code=option.get_text()[:-1:])

    return JsonResponse({"course_codes": [code.code for code in CourseCode.objects.all()]})


@user_passes_test(lambda u: u.is_superuser)
def refresh_courses(request):
    Course.objects.all().delete()

    r = requests.get(BASE_URL + "BLG")
    soup = BeautifulSoup(r.content, "html.parser")

    i = 5
    while True:
        try:
            raw_course = soup.select_one("tr:nth-of-type({})".format(i))
            try:
                data = [row.get_text() for row in raw_course.find_all("td")]
                n = len(data[4]) // 3
                time = data[6][:-1:].split()[i].split("/")
                if "" in time:
                    time = ["2500", "2500"]
                for index in range(n):
                    if time[index][0] == "0":
                        time[index] = time[index][1::]
                    Course.objects.create(
                        crn=int(data[0]),
                        course_code=data[1],
                        title=data[2],
                        instructor=data[3],
                        building=data[4][3*index:3*index+3:],
                        day=data[5].split()[index],
                        time_start=int(time[0]),
                        time_finish=int(time[1]),
                        room=int(data[7].split()[index]),
                        capacity=int(data[8]),
                        enrolled=int(data[9]),
                        reservation=data[10],
                        major_restriction=data[11],
                        prerequisites=data[12],
                        class_restriction=data[13]
                    )
                i += 1
            except AttributeError as error:
                i += 1
                pass
        except IndexError as error:
            break

    return JsonResponse({"courses": serializers.serialize("json", Course.objects.all())})