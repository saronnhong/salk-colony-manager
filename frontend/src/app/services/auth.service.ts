import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { catchError, map, Observable, of, tap } from 'rxjs';

import { CurrentUser } from '../models/current-user.model';
import { environment } from '../../environments/environment';
import { Router } from '@angular/router';

@Injectable({
    providedIn: 'root',
})
export class AuthService {
    private readonly apiUrl =
        `${environment.apiBaseUrl}/api/auth`;

    currentUser = signal<CurrentUser | null>(null);
    loading = signal(false);

    constructor(
        private http: HttpClient,
        private router: Router,
    ) { }

    loadCurrentUser(): void {
        this.loading.set(true);

        this.http.get<CurrentUser>(
            `${this.apiUrl}/me/`,
            {
                withCredentials: true,
            },
        )
            .subscribe({
                next: (user) => {
                    this.currentUser.set(user);
                    this.loading.set(false);
                },

                error: () => {
                    this.currentUser.set(null);
                    this.loading.set(false);
                },
            });
    }

    checkAuthenticated(): Observable<boolean> {
        return this.http.get<CurrentUser>(
            `${this.apiUrl}/me/`,
            {
                withCredentials: true,
            },
        ).pipe(
            tap((user) => {
                this.currentUser.set(user);
            }),
            map(() => true),
            catchError(() => {
                this.currentUser.set(null);
                return of(false);
            }),
        );
    }

    login(): void {
        window.location.href =
            `${environment.apiBaseUrl}/accounts/github/login/`;
    }

    logout(): void {
        this.http.post(
            `${environment.apiBaseUrl}/accounts/logout/`,
            {},
            {
                withCredentials: true,
            },
        ).subscribe({
            next: () => {
                this.currentUser.set(null);
                this.router.navigate(['/login']);
            },

            error: () => {
                this.currentUser.set(null);
                this.router.navigate(['/login']);
            },
        });
    }
}