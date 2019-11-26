import logging

import keyedcache
from django import forms
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

log = logging.getLogger(__name__)

YN = (
    ('Y', _('Yes')),
    ('N', _('No')),
)


class CacheDeleteForm(forms.Form):
    tag = forms.CharField(label=_('Key to delete'), required=False)
    children = forms.ChoiceField(label=_('Include Children?'), choices=YN, initial="Y")
    kill_all = forms.ChoiceField(label=_('Delete all keys?'), choices=YN, initial="Y")

    def delete_cache(self):

        data = self.cleaned_data
        if data['kill_all'] == "Y":
            keyedcache.cache_delete()
            result = "Deleted all keys"
        elif data['tag']:
            keyedcache.cache_delete(data['tag'], children=data['children'])
            if data['children'] == "Y":
                result = "Deleted %s and children" % data['tag']
            else:
                result = "Deleted %s" % data['tag']
        else:
            result = "Nothing selected to delete"

        log.debug(result)
        return result


def stats_page(request):
    calls = keyedcache.CACHE_CALLS
    hits = keyedcache.CACHE_HITS

    if (calls and hits):
        rate = float(keyedcache.CACHE_HITS) / keyedcache.CACHE_CALLS * 100
    else:
        rate = 0

    try:
        running = keyedcache.cache_require()

    except keyedcache.CacheNotRespondingError:
        running = False

    ctx = {
        'cache_count': len(keyedcache.CACHED_KEYS),
        'cache_running': running,
        'cache_time': keyedcache.CACHE_TIMEOUT,
        'cache_backend': keyedcache.cache.__module__,
        'cache_calls': keyedcache.CACHE_CALLS,
        'cache_hits': keyedcache.CACHE_HITS,
        'hit_rate': "%02.1f" % rate
    }

    return render(request, 'keyedcache/stats.html', ctx)


stats_page = user_passes_test(lambda u: u.is_authenticated() and u.is_staff if callable(u.is_authenticated) else u.is_authenticated and u.is_staff, login_url='/accounts/login/')(stats_page)


def view_page(request):
    keys = list(keyedcache.CACHED_KEYS.keys())

    keys.sort()

    ctx = {
        'cached_keys': keys,
    }

    return render(request, 'keyedcache/view.html', ctx)


view_page = user_passes_test(lambda u: u.is_authenticated() and u.is_staff if callable(u.is_authenticated) else u.is_authenticated and u.is_staff, login_url='/accounts/login/')(view_page)


def delete_page(request):
    log.debug("delete_page")
    if request.method == "POST":
        form = CacheDeleteForm(request.POST)
        if form.is_valid():
            log.debug('delete form valid')
            results = form.delete_cache()
            return HttpResponseRedirect('../')
        else:
            log.debug("Errors in form: %s", form.errors)
    else:
        log.debug("new form")
        form = CacheDeleteForm()

    ctx = {
        'form': form,
    }

    return render(request, 'keyedcache/delete.html', ctx)


delete_page = user_passes_test(lambda u: u.is_authenticated() and u.is_staff if callable(u.is_authenticated) else u.is_authenticated and u.is_staff, login_url='/accounts/login/')(delete_page)
