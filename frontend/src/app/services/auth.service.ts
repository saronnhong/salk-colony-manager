import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { CurrentUser } from '../models/current-user.model';

@Injectable({
    providedIn: 'root',
})
export class AuthService {
    private readonly apiUrl =
        'http://localhost:8000/api/auth';

    currentUser = signal<CurrentUser | null>(null);
    loading = signal(false);

    constructor(
        private http: HttpClient,
    ) { }

    loadCurrentUser(): void {
        this.loading.set(true);

        this.http.get<CurrentUser>(
            `${this.apiUrl}/me/`,
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

    login(): void {
        window.location.href =
            'http://localhost:8000/accounts/github/login/';
    }
}