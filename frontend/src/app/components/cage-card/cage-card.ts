import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { CageSummary } from '../../models/cage.model';

@Component({
  selector: 'app-cage-card',
  imports: [RouterLink],
  templateUrl: './cage-card.html',
  styleUrl: './cage-card.scss',
})
export class CageCard {
  @Input({ required: true }) cage!: CageSummary;
}
