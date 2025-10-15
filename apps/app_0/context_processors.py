import os


def site_settings(request):
    return {
        'SITE_NAME': os.environ.get('SITE_NAME', 'JIVAPMS'),
        'SITE_HEADER': os.environ.get('SITE_HEADER', 'JIVAPMS Admin'),
        'BUILD_VERSION': os.environ.get('BUILD_VERSION', '0.1.0'),
        'BUILD_DATE': os.environ.get('BUILD_DATE', ''),
        'SITE_TAGLINE': os.environ.get('SITE_TAGLINE', 'Product and Project Management System'),
    }
