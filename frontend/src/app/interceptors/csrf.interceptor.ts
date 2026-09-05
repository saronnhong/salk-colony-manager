import {
  HttpInterceptorFn,
} from '@angular/common/http';

import { environment } from '../../environments/environment';

function getCookie(name: string): string | null {
  const match = document.cookie
    .split('; ')
    .find((cookie) =>
      cookie.startsWith(`${name}=`),
    );

  if (!match) {
    return null;
  }

  return decodeURIComponent(
    match.substring(name.length + 1),
  );
}

export const csrfInterceptor: HttpInterceptorFn = (
  req,
  next,
) => {
  const isApiRequest =
    req.url.startsWith(environment.apiBaseUrl);

  const isUnsafeMethod = ![
    'GET',
    'HEAD',
    'OPTIONS',
    'TRACE',
  ].includes(req.method);

  if (!isApiRequest || !isUnsafeMethod) {
    return next(req);
  }

  const csrfToken = getCookie('csrftoken');

  if (!csrfToken) {
    return next(req);
  }

  return next(
    req.clone({
      setHeaders: {
        'X-CSRFToken': csrfToken,
      },
      withCredentials: true,
    }),
  );
};