import { useForm } from 'react-hook-form';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Button } from '../ui/button';

export interface MetadataFormData {
  school_id: string;
  region_id: string;
  school_type: string;
  intervention_type: string;
  participant_role: string;
  interview_date: string;
}

interface MetadataFormProps {
  onSubmit: (data: MetadataFormData) => void;
  isLoading?: boolean;
  isFormDisabled?: boolean;
}

export function MetadataForm({ onSubmit, isLoading, isFormDisabled }: MetadataFormProps) {
  const { register, handleSubmit, setValue, formState: { errors } } = useForm<MetadataFormData>();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Metadata</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="school_id">School ID *</Label>
            <Input
              id="school_id"
              {...register('school_id', { required: 'School ID is required' })}
              placeholder="school_001"
            />
            {errors.school_id && (
              <p className="text-sm text-red-600 mt-1">{errors.school_id.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="region_id">Region *</Label>
            <Select onValueChange={(value) => setValue('region_id', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select region" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="praha">Praha</SelectItem>
                <SelectItem value="stredocesky">Středočeský</SelectItem>
                <SelectItem value="jihocesky">Jihočeský</SelectItem>
                <SelectItem value="plzensky">Plzeňský</SelectItem>
                <SelectItem value="karlovarsky">Karlovarský</SelectItem>
                <SelectItem value="ustecky">Ústecký</SelectItem>
                <SelectItem value="liberecky">Liberecký</SelectItem>
                <SelectItem value="kralovehradecky">Královéhradecký</SelectItem>
                <SelectItem value="pardubicky">Pardubický</SelectItem>
                <SelectItem value="olomoucky">Olomoucký</SelectItem>
                <SelectItem value="moravskoslezsky">Moravskoslezský</SelectItem>
                <SelectItem value="jihomoravsky">Jihomoravský</SelectItem>
                <SelectItem value="zlin">Zlín</SelectItem>
                <SelectItem value="vysocina">Vysočina</SelectItem>
              </SelectContent>
            </Select>
            <input type="hidden" {...register('region_id', { required: 'Region is required' })} />
            {errors.region_id && (
              <p className="text-sm text-red-600 mt-1">{errors.region_id.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="school_type">School Type *</Label>
            <Select onValueChange={(value) => setValue('school_type', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select school type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="primary">Primary</SelectItem>
                <SelectItem value="secondary">Secondary</SelectItem>
                <SelectItem value="gymnasium">Gymnasium</SelectItem>
                <SelectItem value="kindergarten">Kindergarten</SelectItem>
                <SelectItem value="special">Special</SelectItem>
              </SelectContent>
            </Select>
            <input type="hidden" {...register('school_type', { required: 'School type is required' })} />
            {errors.school_type && (
              <p className="text-sm text-red-600 mt-1">{errors.school_type.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="intervention_type">Intervention Type *</Label>
            <Select onValueChange={(value) => setValue('intervention_type', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select intervention" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="mentoring_program">Mentoring Program</SelectItem>
                <SelectItem value="leadership_workshop">Leadership Workshop</SelectItem>
                <SelectItem value="team_training">Team Training</SelectItem>
                <SelectItem value="municipal_collaboration">Municipal Collaboration</SelectItem>
                <SelectItem value="teacher_course">Teacher Course</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
            <input type="hidden" {...register('intervention_type', { required: 'Intervention type is required' })} />
            {errors.intervention_type && (
              <p className="text-sm text-red-600 mt-1">{errors.intervention_type.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="participant_role">Participant Role *</Label>
            <Select onValueChange={(value) => setValue('participant_role', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="teacher">Teacher</SelectItem>
                <SelectItem value="principal">Principal</SelectItem>
                <SelectItem value="coordinator">Coordinator</SelectItem>
                <SelectItem value="municipality">Municipality</SelectItem>
              </SelectContent>
            </Select>
            <input type="hidden" {...register('participant_role', { required: 'Participant role is required' })} />
            {errors.participant_role && (
              <p className="text-sm text-red-600 mt-1">{errors.participant_role.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="interview_date">Interview Date *</Label>
            <Input
              id="interview_date"
              type="date"
              {...register('interview_date', { required: 'Interview date is required' })}
            />
            {errors.interview_date && (
              <p className="text-sm text-red-600 mt-1">{errors.interview_date.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full" disabled={isLoading || isFormDisabled}>
            {isLoading ? 'Submitting...' : 'Submit'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

