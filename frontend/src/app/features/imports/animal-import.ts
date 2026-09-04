import {
  Component,
  signal,
} from '@angular/core';

import {
  ImportBatchPreview,
  ImportRowPreview,
} from '../../models/import-preview.model';

import {
  ImportService,
} from '../../services/import.service';

@Component({
  selector: 'app-animal-import',
  standalone: true,
  templateUrl: './animal-import.html',
  styleUrl: './animal-import.scss',
})
export class AnimalImportComponent {
  selectedFile = signal<File | null>(null);

  preview = signal<ImportBatchPreview | null>(
    null,
  );

  loading = signal(false);
  error = signal('');
  committing = signal(false);
  commitMessage = signal('');

  constructor(
    private importService: ImportService,
  ) {}

  onFileSelected(
    event: Event,
  ): void {
    const input = event.target as HTMLInputElement;

    const file =
      input.files?.[0] ?? null;

    this.selectedFile.set(file);
    this.preview.set(null);
    this.error.set('');
  }

  previewImport(): void {
    const file =
      this.selectedFile();

    if (!file) {
      this.error.set(
        'Select a CSV file first.',
      );

      return;
    }

    this.loading.set(true);
    this.error.set('');

    this.importService
      .previewAnimalImport(file)
      .subscribe({
        next: (preview) => {
          this.preview.set(preview);
          this.loading.set(false);
        },

        error: (error) => {
          this.error.set(
            error.error?.detail ??
            'Unable to preview this file.',
          );

          this.loading.set(false);
        },
      });
  }

  rowErrors(
    row: ImportRowPreview,
  ): string[] {
    if (!row.validation_errors) {
      return [];
    }

    return Object.values(
      row.validation_errors,
    );
  }

  validRowCount(): number {
    return (
      this.preview()?.rows.filter(
        (row) =>
          row.parse_status === 'valid',
      ).length ?? 0
    );
  }

  invalidRowCount(): number {
    return (
      this.preview()?.rows.filter(
        (row) =>
          row.parse_status === 'invalid',
      ).length ?? 0
    );
  }

  commitImport(): void {
    const batch = this.preview();

    if (!batch) {
        return;
    }

    this.committing.set(true);
    this.error.set('');
    this.commitMessage.set('');

    this.importService
        .commitAnimalImport(batch.id)
        .subscribe({
        next: (response) => {
            this.preview.set(response.batch);

            this.commitMessage.set(
            `Imported ${response.committed_count} animal` +
            `${response.committed_count === 1 ? '' : 's'}. ` +
            `${response.skipped_count} row` +
            `${response.skipped_count === 1 ? '' : 's'} skipped.`,
            );

            this.committing.set(false);
        },

        error: (error) => {
            this.error.set(
            error.error?.detail ??
            'Unable to import animals.',
            );

            this.committing.set(false);
        },
        });
    }
}