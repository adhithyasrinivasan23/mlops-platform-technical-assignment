import { TestBed } from '@angular/core/testing';
import { ModelsList } from './models-list';
import { ApiService } from '../../core/services/api.service';
import { of } from 'rxjs';
import { provideRouter } from '@angular/router';

describe('ModelsList', () => {
  let apiSpy: any;

  beforeEach(async () => {
    apiSpy = {
      getModels: () => of([{ id: 'm1', name: 'Model 1', owner: 'Test', framework: 'sklearn' }])
    };

    await TestBed.configureTestingModule({
      imports: [ModelsList],
      providers: [
        { provide: ApiService, useValue: apiSpy },
        provideRouter([])
      ]
    }).compileComponents();
  });

  it('should create the component', () => {
    const fixture = TestBed.createComponent(ModelsList);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('should load models on init', () => {
    const fixture = TestBed.createComponent(ModelsList);
    fixture.detectChanges(); // triggers ngOnInit
    const component = fixture.componentInstance;
    
    expect(component.models.length).toBe(1);
    expect(component.models[0].name).toBe('Model 1');
  });
});
