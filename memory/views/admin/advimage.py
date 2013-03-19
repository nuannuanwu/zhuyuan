# -*- coding: utf-8 -*-
#from django.http import HttpResponse
from django.http import Http404
from django.http import HttpResponse
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def upload_image(request):  
    if request.method == 'POST':  
        if "upload_file" in request.FILES:  
            f = request.FILES["upload_file"]  
            name = "/richimage/"+f.name
            path = default_storage.save(name,f)
            url = default_storage.url(path)
            return HttpResponse(url)
    return HttpResponse(u"上传失败！")

