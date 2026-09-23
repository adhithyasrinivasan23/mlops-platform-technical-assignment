import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const snackBar = inject(MatSnackBar);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      let errorMsg = 'An unknown error occurred!';
      
      if (error.error instanceof ErrorEvent) {
        // Client-side error
        errorMsg = `Error: ${error.error.message}`;
      } else {
        // Server-side error
        if (error.error && error.error.detail) {
          // FastAPI specific detail structure
          errorMsg = error.error.detail;
        } else {
          errorMsg = `Error Code: ${error.status}\nMessage: ${error.message}`;
        }
      }

      // Display the error using Material SnackBar
      snackBar.open(errorMsg, 'Close', {
        duration: 5000,
        panelClass: ['error-snackbar'],
        horizontalPosition: 'end',
        verticalPosition: 'bottom'
      });

      return throwError(() => new Error(errorMsg));
    })
  );
};
