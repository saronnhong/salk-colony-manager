// import { Routes } from '@angular/router';

// export const routes: Routes = [];

import { Routes } from '@angular/router';

import { CageList } from './pages/cage-list/cage-list';
import { CageDetail } from './pages/cage-detail/cage-detail';
import { AnimalDetail } from './components/animal-detail/animal-detail';
import { Login } from './pages/login/login';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'cages',
    pathMatch: 'full'
  },

  {
    path: 'login',
    component: Login
  },

  {
    path: 'cages',
    component: CageList,
    canActivate: [authGuard]
  },

  {
    path: 'cages/:id',
    component: CageDetail,
    canActivate: [authGuard]
  },

  {
    path: 'animals/:id',
    component: AnimalDetail,
    canActivate: [authGuard]
  },

  {
    path: 'imports/animals',
    loadComponent: () =>
      import(
        './features/imports/animal-import'
      ).then(
        (m) => m.AnimalImportComponent,
      ),
    canActivate: [authGuard]
  },

  {
    path: '**',
    redirectTo: 'cages'
  }
];
