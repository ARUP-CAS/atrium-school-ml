/**
 * Post-school feedback form — AIS CR Computer Vision Training School.
 *
 * Google Apps Script. To build the form:
 *   1. script.google.com  ->  New project
 *   2. paste this file in, save
 *   3. Run  createFeedbackForm  (authorise it the first time)
 *   4. The edit and public URLs are printed to the execution log
 *
 * Creates the form only. To collect answers in a spreadsheet, open the form,
 * Responses -> Link to Sheets. Re-running makes a *second*, separate form.
 *
 * No e-mail addresses are collected and the name field at the end is optional,
 * so responses are anonymous unless someone chooses otherwise. Participants
 * have already consented to their feedback being quoted, so no consent item.
 *
 * The lecturer questions exist to give each person something concrete to work
 * with for their next workshop — keep the wording forward-looking if you edit.
 */

const FORM_TITLE = 'CV in Archaeology — Post-School Survey';

const FORM_DESCRIPTION = [
  'Thank you for the week! This takes about five minutes.',
  '',
  'We use it for two things: to plan a better school next time, and to give each',
  'of the five people who taught something concrete to work on for their next',
  'workshop. It is not a grading exercise — "this part lost me" is the single most',
  'useful thing you can write.',
  '',
  'No e-mail address is collected. The name field at the very end is optional.',
].join('\n');

/** Row labels for the two session grids, and the per-session comment boxes. */
const SESSIONS = [
  'Petr — Introduction, annotation & artefacts',
  'Ronald — Coding with agents & coins',
  'Anastasia — ML basics & microscopic data',
  'Ashely — Rock art',
  'Filip — Python & remote sensing',
];

const GRID_SCALE = ['1', '2', '3', '4', '5', 'Missed this one'];

function createFeedbackForm() {
  const form = FormApp.create(FORM_TITLE)
    .setTitle(FORM_TITLE)
    .setDescription(FORM_DESCRIPTION)
    .setProgressBar(true)
    .setAllowResponseEdits(false)
    .setLimitOneResponsePerUser(false)
    .setShowLinkToRespondAgain(false)
    .setConfirmationMessage(
      'Thank you — this goes straight into planning the next one.');

  doNotCollectEmail(form);

  // ---- The week, in two numbers ------------------------------------------
  // The only two required items: they are the figures worth comparing between
  // rounds, and everything else stays optional to keep completion high.
  form.addScaleItem()
    .setTitle('I am happy with what I learned this week')
    .setBounds(1, 5)
    .setLabels('Not really', 'Very happy')
    .setRequired(true);

  form.addScaleItem()
    .setTitle('When I got stuck, help was there when I needed it')
    .setBounds(1, 5)
    .setLabels('Rarely', 'Always')
    .setRequired(true);

  // ---- The sessions -------------------------------------------------------
  form.addPageBreakItem()
    .setTitle('The sessions')
    .setHelpText(
      'Five people taught this week. Use "Missed this one" for anything you ' +
      'were not in the room for.');

  form.addGridItem()
    .setTitle('It was easy to follow along and understand')
    .setHelpText('1 = I lost the thread early on, 5 = I could follow throughout.')
    .setRows(SESSIONS)
    .setColumns(GRID_SCALE);

  form.addGridItem()
    .setTitle('The way the session was run worked for me')
    .setHelpText(
      'The teaching format rather than the topic — Colab notebooks to follow ' +
      'along in, live coding, working alone at your own pace, demonstrations, ' +
      'working in pairs. 1 = did not suit me at all, 5 = suited me well.')
    .setRows(SESSIONS)
    .setColumns(GRID_SCALE);

  SESSIONS.forEach(function (session) {
    form.addParagraphTextItem()
      .setTitle(session)
      .setHelpText(
        'Optional. What worked, and what would make this session easier to ' +
        'learn from next time?');
  });

  // ---- The week overall ---------------------------------------------------
  form.addPageBreakItem().setTitle('The week overall');

  form.addMultipleChoiceItem()
    .setTitle('The pace of the week was')
    .setChoiceValues(
      ['Too slow', 'A bit slow', 'About right', 'A bit fast', 'Too fast']);

  form.addMultipleChoiceItem()
    .setTitle('Five days was')
    .setChoiceValues(['Too short', 'About right', 'Too long']);

  form.addScaleItem()
    .setTitle('The setup guide and what we sent before the school prepared me well')
    .setBounds(1, 5)
    .setLabels('Not at all', 'Fully');

  form.addScaleItem()
    .setTitle('I expect to come back to the slides and notebooks after the school')
    .setBounds(1, 5)
    .setLabels('Unlikely', 'Certainly');

  form.addGridItem()
    .setTitle('How well did the practical side work?')
    .setHelpText('1 = badly, 5 = well.')
    .setRows([
      'Room, wifi and equipment',
      'Food and coffee breaks',
      'Evening programme (ice-breaker, city walk, social event)',
      'Travel and accommodation information',
    ])
    .setColumns(GRID_SCALE.slice(0, 5).concat(['Not applicable']));

  // ---- Free text ----------------------------------------------------------
  form.addPageBreakItem()
    .setTitle('In your own words')
    .setHelpText('All optional — write as much or as little as you like.');

  form.addParagraphTextItem()
    .setTitle('What did you enjoy most? What should we keep exactly as it was?');

  form.addParagraphTextItem()
    .setTitle('What did not work for you, and what should we change next time?');

  form.addParagraphTextItem()
    .setTitle('If you were organising the school, what would you do differently?');

  form.addParagraphTextItem()
    .setTitle('Anything else you would like to tell us?');

  form.addTextItem()
    .setTitle('Your name')
    .setHelpText(
      'Optional, and only if you would like us to be able to follow up with ' +
      'you. Leave it blank to stay anonymous.');

  Logger.log('Edit:   %s', form.getEditUrl());
  Logger.log('Share:  %s', form.getPublishedUrl());
  return form;
}

/**
 * Turn off e-mail collection. setCollectEmail() is deprecated in newer runtimes
 * in favour of setEmailCollectionType(), so try the new API first.
 */
function doNotCollectEmail(form) {
  if (FormApp.EmailCollectionType && form.setEmailCollectionType) {
    form.setEmailCollectionType(FormApp.EmailCollectionType.DO_NOT_COLLECT);
  } else {
    form.setCollectEmail(false);
  }
}
