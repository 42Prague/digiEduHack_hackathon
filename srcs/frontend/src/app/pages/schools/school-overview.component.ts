import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/auth.service';
import { MockChartsComponent } from '../../components/mock-charts/mock-charts.component';
import { AiChatComponent } from '../../components/ai-chat/ai-chat.component';
import { TranslateModule } from '@ngx-translate/core';

@Component({
	selector: 'app-school-overview',
	standalone: true,
	imports: [CommonModule, MockChartsComponent, AiChatComponent, TranslateModule],
	templateUrl: './school-overview.component.html',
	styleUrls: ['./school-overview.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class SchoolOverviewComponent implements OnInit {
	// #region Public Properties
	// #endregion

	// #region Private Properties
	private readonly auth: AuthService = inject(AuthService);
	// #endregion

	// #region Public Methods
	public ngOnInit(): void {
		// no-op: charts and chat are mock components
	}
	// #endregion
}

