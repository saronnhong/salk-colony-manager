import { HttpInterceptorFn } from '@angular/common/http';

function getCookie(name: string): string | null {
  const cookies = document.cookie
    .split(';')
    .map((cookie) => cookie.trim());

  const cookie = cookies.find(
    (item) => item.startsWith(`${name}=`)
  );

  if (!cookie) {
    return null;
  }

  return decodeURIComponent(
    cookie.substring(name.length + 1)
  );
}

export const credentialsInterceptor: HttpInterceptorFn = (
  request,
  next,
) => {
  let updatedRequest = request.clone({
    withCredentials: true,
  });

  const unsafeMethod = ![
    'GET',
    'HEAD',
    'OPTIONS',
  ].includes(request.method);

  if (unsafeMethod) {
    const csrfToken = getCookie('csrftoken');

    if (csrfToken) {
      updatedRequest = updatedRequest.clone({
        setHeaders: {
          'X-CSRFToken': csrfToken,
        },
      });
    }
  }

  return next(updatedRequest);
};