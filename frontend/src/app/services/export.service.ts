import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';

@Injectable({
    providedIn: 'root',
})
export class ExportService {
    private readonly apiUrl = `${environment.apiBaseUrl}/api/exports`;

    constructor(
        private http: HttpClient,
    ) { }

    downloadAnimalCensus(): void {
        this.http.get(
            `${this.apiUrl}/animal-census.csv`,
            {
                responseType: 'blob',
            },
        ).subscribe({
            next: (blob) => {
                const url =
                    window.URL.createObjectURL(blob);

                const link =
                    document.createElement('a');

                link.href = url;
                link.download = 'animal_census.csv';

                document.body.appendChild(link);
                link.click();
                link.remove();

                window.URL.revokeObjectURL(url);
            },

            error: () => {
                console.error(
                    'Unable to download animal census.',
                );
            },
        });
    }
}