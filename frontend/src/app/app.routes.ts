import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'models', pathMatch: 'full' },
  {
    path: 'models',
    loadComponent: () => import('./features/models-list/models-list').then(m => m.ModelsList)
  },
  {
    path: 'models/:id',
    loadComponent: () => import('./features/model-detail/model-detail').then(m => m.ModelDetail)
  },
  {
    path: 'deployments',
    loadComponent: () => import('./features/deployments-list/deployments-list').then(m => m.DeploymentsList)
  }
];
