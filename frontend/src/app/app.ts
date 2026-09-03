import { Component, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App implements OnInit {
    constructor(
    public authService: AuthService,
  ) {}

  ngOnInit(): void {
    this.authService.loadCurrentUser();
  }
 }
