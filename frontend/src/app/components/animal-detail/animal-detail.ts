import { Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import {
  FormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';

import { CageSummary } from '../../models/cage.model';
import { CageService } from '../../services/cage.service';

import {
  AnimalDetailModel,
  AnimalLocationHistory,
} from '../../models/animal.model';
import { AnimalService } from '../../services/animal.service';

import {
  HusbandryEventType,
  HusbandryEvent,
} from '../../models/husbandry-event.model';

import {
  HusbandryEventService,
} from '../../services/husbandry-event.service';

@Component({
  selector: 'app-animal-detail',
  imports: [DatePipe, RouterLink, ReactiveFormsModule],
  templateUrl: './animal-detail.html',
  styleUrl: './animal-detail.scss',
})
export class AnimalDetail implements OnInit {
  private fb = inject(FormBuilder);
  animal = signal<AnimalDetailModel | null>(null);
  eventFormVisible = signal(false);
  savingEvent = signal(false);
  eventError = signal<string | null>(null);
  eventSuccess = signal<string | null>(null);
  husbandryEvents = signal<HusbandryEvent[]>([]);

  locationHistory =
    signal<AnimalLocationHistory[]>([]);

  loading = signal(true);
  error = signal<string | null>(null);

  cages = signal<CageSummary[]>([]);
  moveFormVisible = signal(false);
  moving = signal(false);
  moveError = signal<string | null>(null);
  moveSuccess = signal<string | null>(null);

  moveForm = this.fb.group({
    destination_cage_id: ['', Validators.required],
    reason: [''],
  });

  eventTypes: {
    value: HusbandryEventType;
    label: string;
  }[] = [
      {
        value: 'health_check',
        label: 'Health check',
      },
      {
        value: 'weight',
        label: 'Weight',
      },
      {
        value: 'treatment',
        label: 'Treatment',
      },
      {
        value: 'death',
        label: 'Death',
      },
    ];

  eventForm = this.fb.group({
    event_type: [
      '' as HusbandryEventType | '',
      Validators.required,
    ],
    event_datetime: [
      this.getLocalDateTime(),
      Validators.required,
    ],
    notes: [''],

    weight_grams: [
      null as number | null,
    ],

    treatment_name: [''],

    dose: [''],

    route: [''],
  });

  eventFilter = signal<
    'today' | 'yesterday' | 'all'
  >('today');

  constructor(
    private route: ActivatedRoute,
    private animalService: AnimalService,
    private cageService: CageService,
    private husbandryEventService: HusbandryEventService,
  ) { }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');

    if (!id) {
      this.error.set('Animal ID was not provided.');
      this.loading.set(false);
      return;
    }

    this.loadAnimal(id);
    this.loadLocationHistory(id);
    this.loadCages();
    this.loadHusbandryEvents(id);
  }

  private loadAnimal(id: string): void {
    this.animalService.getAnimal(id).subscribe({
      next: animal => {
        this.animal.set(animal);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Unable to load animal.');
        this.loading.set(false);
      },
    });
  }

  private loadLocationHistory(id: string): void {
    this.animalService
      .getLocationHistory(id)
      .subscribe({
        next: history => {
          this.locationHistory.set(history);
        },
        error: () => {
          this.locationHistory.set([]);
        },
      });
  }

  private loadCages(): void {
    this.cageService.getCages().subscribe({
      next: cages => {
        this.cages.set(cages);
      },
      error: () => {
        this.cages.set([]);
      },
    });
  }

  showMoveForm(): void {
    this.moveError.set(null);
    this.moveSuccess.set(null);
    this.moveFormVisible.set(true);
  }

  cancelMove(): void {
    this.moveFormVisible.set(false);
    this.moveError.set(null);

    this.moveForm.reset({
      destination_cage_id: '',
      reason: '',
    });
  }

  submitMove(): void {
    if (this.moveForm.invalid) {
      this.moveForm.markAllAsTouched();
      return;
    }

    const animal = this.animal();

    if (!animal) {
      return;
    }

    const destinationCageId =
      this.moveForm.controls.destination_cage_id.value;

    if (!destinationCageId) {
      return;
    }

    this.moving.set(true);
    this.moveError.set(null);
    this.moveSuccess.set(null);

    this.animalService.moveAnimal(
      animal.id,
      {
        destination_cage_id: destinationCageId,
        reason:
          this.moveForm.controls.reason.value || '',
      }
    ).subscribe({
      next: updatedAnimal => {
        this.animal.set(updatedAnimal);

        this.moveSuccess.set(
          `Animal moved to ${updatedAnimal.current_location?.cage_code
          ?? 'new cage'
          }.`
        );

        this.moveFormVisible.set(false);
        this.moving.set(false);

        this.moveForm.reset({
          destination_cage_id: '',
          reason: '',
        });

        this.loadLocationHistory(updatedAnimal.id);
      },
      error: error => {
        console.error('Move animal error:', error);

        const detail = error?.error?.detail;

        this.moveError.set(
          Array.isArray(detail)
            ? detail.join(' ')
            : detail ||
            error?.error?.message ||
            `Unable to move animal. Server returned ${error.status}.`
        );

        this.moving.set(false);
      },
    });
  }

  private getLocalDateTime(): string {
    const now = new Date();

    const offset =
      now.getTimezoneOffset() * 60_000;

    return new Date(
      now.getTime() - offset
    )
      .toISOString()
      .slice(0, 16);
  }

  showEventForm(): void {
    this.eventError.set(null);
    this.eventSuccess.set(null);

    this.eventForm.reset({
      event_type: '',
      event_datetime: this.getLocalDateTime(),
      notes: '',
      weight_grams: null,
      treatment_name: '',
      dose: '',
      route: '',
    });

    this.eventFormVisible.set(true);
  }

  cancelEvent(): void {
    this.eventFormVisible.set(false);
    this.eventError.set(null);
  }

  submitEvent(): void {
    if (this.eventForm.invalid) {
      this.eventForm.markAllAsTouched();
      return;
    }

    const animal = this.animal();

    if (!animal) {
      return;
    }

    const eventType =
      this.eventForm.controls.event_type.value;

    const eventDateTime =
      this.eventForm.controls.event_datetime.value;

    if (!eventType || !eventDateTime) {
      return;
    }

    this.savingEvent.set(true);
    this.eventError.set(null);
    this.eventSuccess.set(null);

    const formValue = this.eventForm.getRawValue();

    this.husbandryEventService.createEvent({
      event_type: eventType,
      animal: animal.id,
      event_datetime: new Date(
        eventDateTime
      ).toISOString(),
      notes: formValue.notes || '',
      metadata: {},
      ...(eventType === 'weight' &&
        formValue.weight_grams !== null
        ? {
          weight_grams:
            formValue.weight_grams,
        }
        : {}),

      ...(eventType === 'treatment'
        ? {
          treatment_name:
            formValue.treatment_name || '',
          dose:
            formValue.dose || '',
          route:
            formValue.route || '',
        }
        : {}),
    }).subscribe({
      next: event => {
        this.eventSuccess.set(
          `${this.getEventLabel(event.event_type)} recorded.`
        );

        this.eventFormVisible.set(false);
        this.savingEvent.set(false);

        this.loadHusbandryEvents(animal.id);
      },

      error: error => {
        console.error(
          'Create husbandry event error:',
          error
        );

        const detail = error?.error?.detail;

        this.eventError.set(
          Array.isArray(detail)
            ? detail.join(' ')
            : detail ||
            `Unable to record event. Server returned ${error.status}.`
        );

        this.savingEvent.set(false);
      },
    });
  }

  getEventLabel(
    eventType: HusbandryEventType
  ): string {
    return (
      this.eventTypes.find(
        option => option.value === eventType
      )?.label ?? eventType
    );
  }

  private loadHusbandryEvents(
    animalId: string
  ): void {
    this.husbandryEventService
      .getEventsForAnimal(animalId)
      .subscribe({
        next: events => {
          this.husbandryEvents.set(events);
        },
        error: () => {
          this.husbandryEvents.set([]);
        },
      });
  }

  setEventFilter(
    filter: 'today' | 'yesterday' | 'all'
  ): void {
    this.eventFilter.set(filter);
  }

  filteredHusbandryEvents(): HusbandryEvent[] {
    const filter = this.eventFilter();

    if (filter === 'all') {
      return this.husbandryEvents();
    }

    const now = new Date();

    const targetDate = new Date(now);

    if (filter === 'yesterday') {
      targetDate.setDate(
        targetDate.getDate() - 1
      );
    }

    return this.husbandryEvents().filter(event => {
      const eventDate =
        new Date(event.event_datetime);

      return (
        eventDate.getFullYear() ===
        targetDate.getFullYear() &&
        eventDate.getMonth() ===
        targetDate.getMonth() &&
        eventDate.getDate() ===
        targetDate.getDate()
      );
    });
  }
}
