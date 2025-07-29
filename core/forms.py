from django import forms

class SearchUrlForm(forms.Form):
    reverb_url = forms.CharField(max_length=2000, widget=forms.TextInput(
            attrs={
                "placeholder": "Reverb search URL",
            }
        )
    )

    def clean_reverb_url(self):
        value = self.cleaned_data["reverb_url"]
        valid_url_startswith = "https://reverb.com/marketplace?query="
        if not value.startswith(valid_url_startswith):
            raise forms.ValidationError(
                f"Enter a valid reverb.com search URL. Hint: It should start with {valid_url_startswith}"
            )
        return value
