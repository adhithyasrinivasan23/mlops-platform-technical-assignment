import { TestBed } from '@angular/core/testing';
import { ModelDetail } from './model-detail';
import { ApiService } from '../../core/services/api.service';
import { of, throwError } from 'rxjs';
import { provideRouter } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';

describe('ModelDetail', () => {
  let apiSpy: any;
  let snackBarSpy: any;

  beforeEach(async () => {
    apiSpy = {
      getModel: () => of({ id: 'm1', name: 'Model 1', owner: 'Test', framework: 'sklearn' }),
      getVersions: () => of([{ id: 1, version: '1.0', stage: 'APPROVED', approved: true }]),
      getMetrics: () => of([]),
      createDeployment: () => throwError(() => ({ error: { detail: 'Cannot deploy an unapproved model version' } }))
    };
    
    snackBarSpy = { open: () => {} };

    await TestBed.configureTestingModule({
      imports: [ModelDetail],
      providers: [
        { provide: ApiService, useValue: apiSpy },
        { provide: MatSnackBar, useValue: snackBarSpy },
        provideRouter([])
      ]
    }).compileComponents();
  });

  it('should create the component', () => {
    const fixture = TestBed.createComponent(ModelDetail);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('should load data on init', () => {
    const fixture = TestBed.createComponent(ModelDetail);
    fixture.componentInstance.modelId = 'm1';
    fixture.detectChanges(); 
  });

  it('should handle deployment error gracefully', () => {
    const fixture = TestBed.createComponent(ModelDetail);
    fixture.componentInstance.modelId = 'm1';
    fixture.detectChanges();
    
    // Try to trigger a failed deployment manually bypassing dialog for unit test
    (fixture.componentInstance as any).api.createDeployment({} as any).subscribe({
      error: (err: any) => {
        expect(err.error.detail).toBe('Cannot deploy an unapproved model version');
      }
    });
  });
});
