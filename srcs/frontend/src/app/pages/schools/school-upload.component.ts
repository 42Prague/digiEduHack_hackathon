import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DataService } from '../../services/data.service';
import { FancyUploadComponent } from '../../components/fancy-upload/fancy-upload.component';

@Component({
	selector: 'app-school-upload',
	standalone: true,
	imports: [CommonModule, FormsModule, FancyUploadComponent],
	templateUrl: './school-upload.component.html',
	styleUrls: ['./school-upload.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class SchoolUploadComponent {
	// #region Public Properties
	public schoolId: string = 's-1';
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
		if (!this.schoolId || !this.file) {
			this.message = 'Please select school and file.';
			return;
		}
		this.dataService.upload('school', this.schoolId, this.file).subscribe((res: { id: string; scopeId: string }) => {
			this.message = `Uploaded dataset ${res.id} for ${res.scopeId}`;
		});
	}
	// #endregion
}

