// import { Routes } from '@angular/router';

// export const routes: Routes = [];

import { Routes } from '@angular/router';

import { CageList } from './pages/cage-list/cage-list';
import { CageDetail } from './pages/cage-detail/cage-detail';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'cages',
    pathMatch: 'full'
  },
  {
    path: 'cages',
    component: CageList
  },
  {
    path: 'cages/:id',
    component: CageDetail
  },
  {
    path: '**',
    redirectTo: 'cages'
  }
];
