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
}