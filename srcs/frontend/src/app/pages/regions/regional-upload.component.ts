import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DataService } from '../../services/data.service';
import { FancyUploadComponent } from '../../components/fancy-upload/fancy-upload.component';

@Component({
	selector: 'app-regional-upload',
	standalone: true,
	imports: [CommonModule, FormsModule, FancyUploadComponent],
	templateUrl: './regional-upload.component.html',
	styleUrls: ['./regional-upload.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class RegionalUploadComponent {
	// #region Public Properties
	public regionId: string = 'r-1';
	public file?: File;
	public message?: string;
	// #endregion

	// #region Private Properties
	private readonly dataService: DataService = inject(DataService);
	// #endregion

	// #region Public Methods
	public handleFile(input: Event): void {
		const el = input.target as HTMLInputElement;
		this.file = el.files?.[0] ?? undefined;
	}

	public upload(): void {
		if (!this.regionId || !this.file) {
			this.message = 'Please select region and file.';
			return;
		}
		this.dataService.upload('region', this.regionId, this.file).subscribe((res: { id: string; scopeId: string }) => {
			this.message = `Uploaded dataset ${res.id} for ${res.scopeId}`;
		});
	}
	// #endregion
}

