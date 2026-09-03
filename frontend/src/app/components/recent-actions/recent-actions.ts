import { DatePipe } from '@angular/common';
import {
  Component,
  OnInit,
  signal,
} from '@angular/core';

import { AuditOperation } from '../../models/audit-operation.model';
import { AuditOperationService } from '../../services/audit-operation.service';

@Component({
  selector: 'app-recent-actions',
  imports: [
    DatePipe,
  ],
  templateUrl: './recent-actions.html',
  styleUrl: './recent-actions.scss',
})
export class RecentActions implements OnInit {
  operations = signal<AuditOperation[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);
  success = signal<string | null>(null);
  undoingId = signal<number | null>(null);

  constructor(
    private auditOperationService: AuditOperationService,
  ) { }

  ngOnInit(): void {
    this.loadOperations();
  }

  loadOperations(): void {
    this.loading.set(true);
    this.error.set(null);

    this.auditOperationService
      .getOperations()
      .subscribe({
        next: (operations) => {
          this.operations.set(
            operations.slice(0, 15)
          );

          this.loading.set(false);
        },
        error: () => {
          this.error.set(
            'Unable to load recent actions.'
          );

          this.loading.set(false);
        },
      });
  }

  undo(operation: AuditOperation): void {
    if (!operation.can_undo) {
      return;
    }

    this.undoingId.set(operation.id);
    this.error.set(null);
    this.success.set(null);

    this.auditOperationService
      .undoOperation(operation.id)
      .subscribe({
        next: () => {
          this.success.set(
            'Action undone successfully.'
          );

          this.undoingId.set(null);

          // Reload because undoing one operation can
          // make an earlier operation undoable again.
          this.loadOperations();
        },
        error: (error) => {
          this.error.set(
            error?.error?.detail ??
            'Unable to undo this action.'
          );

          this.undoingId.set(null);
        },
      });
  }

  actionLabel(operation: AuditOperation): string {
    if (operation.reverses_operation !== null) {
      if (operation.operation_type === 'animal_move') {
        return 'Undid animal move';
      }

      if (operation.operation_type === 'cage_move') {
        return 'Undid cage move';
      }

      return 'Undid action';
    }

    if (operation.operation_type === 'animal_move') {
      return 'Moved animal';
    }

    if (operation.operation_type === 'cage_move') {
      return 'Moved cage';
    }

    return operation.operation_type.replaceAll(
      '_',
      ' ',
    );
  }
}
