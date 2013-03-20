# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render_to_response, redirect, render, get_object_or_404
from memory import helpers
from django.conf import settings

from django.core.urlresolvers import resolve, reverse
import sys, socket   
import oss.oss_api
import oss.oss_util

def test(request):
    SAE_TEST_APPNAME = settings.SAE_TEST_APPNAME
    print SAE_TEST_APPNAME,'SAE_TEST_APPNAME'
    return HttpResponse()



