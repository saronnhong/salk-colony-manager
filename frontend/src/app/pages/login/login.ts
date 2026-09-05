import { Component } from '@angular/core';

import { AuthService } from '../../services/auth.service';

@Component({
    selector: 'app-login',
    standalone: true,
    templateUrl: './login.html',
    styleUrl: './login.scss',
})
export class Login {
    constructor(
        public authService: AuthService,
    ) {}

    login(): void {
        this.authService.login();
    }
}