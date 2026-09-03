export interface CageLocation {
  room: string;
  rack: string;
  position: string;
  valid_from: string;
}

export interface CageSummary {
  id: string;
  cage_code: string;
  cage_type: string;
  current_location: CageLocation | null;
  animal_count: number;
  primary_owner: CageOwner | null;
  current_coverage: CageCoverage | null;
}

export interface AnimalSummary {
  id: string;
  identifier: string | null;
  sex: string;
  date_of_birth: string | null;
  species: string;
}

export interface CageDetailLocation {
  room: {
    id: number;
    name: string;
  };
  rack: {
    id: number;
    rack_code: string;
  };
  position: {
    id: number;
    position_label: string;
  };
  valid_from: string;
}

export interface CageDetailModel {
  id: string;
  cage_code: string;
  cage_type: string;
  notes: string;
  retired_at: string | null;
  created_at: string;
  current_location: CageDetailLocation | null;
  animals: AnimalSummary[];
  primary_owner: CageOwner | null;
  current_coverage: CageCoverage | null;
}

export interface CageOwner {
  id: number;
  name: string;
}

export interface CageCoverage {
  id: number;
  name: string;
  valid_from: string;
  valid_to: string | null;
}

export interface CageMoveRequest {
  destination_rack_position_id: number;
  moved_at?: string;
  reason?: string;
}

export interface RackPositionSummary {
  id: number;
  room: string | null;
  rack: string;
  position_label: string;
  occupied: boolean;
}

export interface CageLocationHistory {
  id: number;
  room: string | null;
  rack: string;
  position: string;
  valid_from: string;
  valid_to: string | null;
  system_from: string;
  system_to: string | null;
  reason: string;
}