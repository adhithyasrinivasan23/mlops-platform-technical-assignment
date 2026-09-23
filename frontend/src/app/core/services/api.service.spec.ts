import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ApiService } from './api.service';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ApiService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should retrieve models', () => {
    const mockModels = [{ id: 'm1', name: 'Model 1', owner: 'Test', framework: 'sklearn' }];
    service.getModels().subscribe(models => {
      expect(models.length).toBe(1);
      expect(models).toEqual(mockModels);
    });

    const req = httpMock.expectOne('/api/models');
    expect(req.request.method).toBe('GET');
    req.flush(mockModels);
  });

  it('should call approve endpoint', () => {
    const mockVersion = { id: 1, version: '1.0', stage: 'APPROVED', approved: true };
    service.approveVersion('m1', 1).subscribe(version => {
      expect(version.approved).toBe(true);
    });

    const req = httpMock.expectOne('/api/models/m1/versions/1/approve');
    expect(req.request.method).toBe('POST');
    req.flush(mockVersion);
  });
});
